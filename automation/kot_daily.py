"""
daily-kot-comparison — ported from SKILL.md to plain Python.

  BEFORE:  ~80 browser tool calls. Name Box navigation at 650ms/cell, clipboard
           TSV pastes that could land a row off, "anti-stale-copy guards" because
           the 21-22 May runs silently duplicated the previous day's tab.
  AFTER:   ~20 HTTP requests + 3 Sheets API calls. Deterministic.

Usage
  python kot_daily.py --dry-run          pull + show what WOULD be written
  python kot_daily.py --selftest         verify the Petpooja client still works
  python kot_daily.py                    do it for real
  python kot_daily.py --date 2026-07-13  backfill a specific business day
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, date, timedelta, timezone

import config
from petpooja import Petpooja, KotResult, SessionExpired, ScrapeError
from sheets import Sheets, a1

IST = timezone(timedelta(hours=5, minutes=30))

# Distinctive token per outlet, used to verify the source tab's column A really
# is in the order we think it is before we write anything into B/C.
MATCH_TOKEN = {
    349767: "dlf",
    159181: "rajinder",
    62697:  "dwarka",
    19652:  "janakpuri",
    16011:  "karkardooma",
    80991:  "noida",
    9960:   "prashant",
    369621: "sector 15",
    62695:  "shivalik",
}


# ---------------------------------------------------------------------------
# dates
# ---------------------------------------------------------------------------
def ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def date_label(d: date) -> str:
    """'13th July' — the tab name and the destination column-A label."""
    return f"{ordinal(d.day)} {d.strftime('%B')}"


def _kot_fmt(d: date) -> str:
    """Petpooja's KOT date box: '13 Jul 2026 01:00:00' (no zero-padded day)."""
    return f"{d.day} {d.strftime('%b %Y')} 01:00:00"


def windows(business_day: date):
    """Petpooja business day runs 01:00 -> 01:00 the next day."""
    nxt = business_day + timedelta(days=1)
    return {
        "kot_from": _kot_fmt(business_day),
        "kot_to":   _kot_fmt(nxt),
        # Captain report format: "2026-07-13 01:00:00"
        "cap_from": business_day.strftime("%Y-%m-%d 01:00:00"),
        "cap_to":   nxt.strftime("%Y-%m-%d 01:00:00"),
    }


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------
def pull(pp: Petpooja, business_day: date) -> list[KotResult]:
    w = windows(business_day)
    results: list[KotResult] = []
    for oid in config.KOT_OUTLETS:
        total = pp.kot_count(oid, w["kot_from"], w["kot_to"])
        captain = pp.captain_kots(oid, w["cap_from"], w["cap_to"])
        r = KotResult(oid, total, captain)
        results.append(r)
        print(f"  {config.SHORT[oid]:<20} KOT {total:>5}   Captain {captain:>5}   {r.captain_pct:>6.2f}%")
    return results


def sanity(results: list[KotResult]) -> list[str]:
    problems = []
    for r in results:
        if r.captain_kot > r.total_kot:
            problems.append(
                f"{config.SHORT[r.outlet_id]}: Captain ({r.captain_kot}) > Total KOT "
                f"({r.total_kot}) — impossible, refusing to write"
            )
        if r.total_kot == 0:
            problems.append(f"{config.SHORT[r.outlet_id]}: zero KOTs — check the outlet")
    return problems


# ---------------------------------------------------------------------------
# source sheet
# ---------------------------------------------------------------------------
def source_plan(sh: Sheets, results: list[KotResult], label: str, dry: bool):
    sid = config.KOT_SOURCE_SHEET_ID
    tabs = sh.tabs(sid)
    titles = [t["title"] for t in tabs]
    newest = min(tabs, key=lambda t: t["index"])["title"]

    exists = label in titles
    print(f"\nSOURCE  {'tab exists' if exists else f'duplicate {newest!r} -> {label!r} at index 0'}")

    if dry:
        print(f"  would write {label!r}!A1        = {label}")
        print(f"  would write {label!r}!B2:C10    = 9 rows (Total KOT, Captain App KOT)")
        print("  row 11 SUM + column D coverage formulas: left untouched (they recalc)")
        return None

    if not exists:
        sh.duplicate_tab(sid, newest, label, index=0)

    # Verify column A really is in the order we assume BEFORE writing B/C.
    col_a = sh.read_range(sid, a1(label, "A2:A10"))
    names = [(row[0] if row else "") for row in col_a]
    for i, oid in enumerate(config.KOT_OUTLETS):
        got = str(names[i]).lower() if i < len(names) else ""
        if MATCH_TOKEN[oid] not in got:
            raise ScrapeError(
                f"source tab {label!r} row {i+2}: expected {config.SHORT[oid]} "
                f"(token {MATCH_TOKEN[oid]!r}), found {got!r}. "
                "Sheet layout changed — aborting before any write."
            )

    by_id = {r.outlet_id: r for r in results}
    rows = [[by_id[oid].total_kot, by_id[oid].captain_kot] for oid in config.KOT_OUTLETS]

    sh.batch_write(sid, {
        a1(label, "A1"): [[label]],
        a1(label, "B2:C10"): rows,
    })

    # Anti-stale-copy guard: the duplicated tab starts life holding YESTERDAY's
    # numbers. Read back and prove ours actually landed.
    back = sh.read_range(sid, a1(label, "B2:C10"))
    for i, oid in enumerate(config.KOT_OUTLETS):
        want = [by_id[oid].total_kot, by_id[oid].captain_kot]
        got = [int(x) for x in back[i]] if i < len(back) else []
        if got != want:
            raise ScrapeError(
                f"source readback mismatch at {config.SHORT[oid]}: "
                f"wrote {want}, sheet says {got}"
            )
    print(f"  wrote + verified B2:C10 on {label!r}")
    return sh.tab_gid(sid, label)


# ---------------------------------------------------------------------------
# destination sheet
# ---------------------------------------------------------------------------
def find_block(sh: Sheets, label: str) -> tuple[int, str | None]:
    """
    Locate the 3-row block for `label`. Blocks start at row 2 and repeat every 3.
    Returns (top_row, prev_label). Refuses to hand back a block that already has data.
    """
    sid, tab = config.SALES_DATA_SHEET_ID, config.KOT_DEST_TAB
    colA = sh.read_range(sid, a1(tab, "A1:A400"))
    flat = [(row[0] if row else "") for row in colA]

    top = config.KOT_DEST_FIRST_BLOCK_ROW
    step = config.KOT_DEST_BLOCK_HEIGHT

    last_filled = None
    r = top
    while r <= len(flat):
        val = str(flat[r - 1]).strip()
        if val == label:
            prev = str(flat[r - 1 - step]).strip() if r - 1 - step >= 0 else None
            return r, prev
        if val:
            last_filled = r
        r += step

    if last_filled is None:
        raise ScrapeError(f"{tab!r}: no filled date blocks found — layout changed?")

    target = last_filled + step
    prev = str(flat[last_filled - 1]).strip()
    return target, prev


def dest_plan(sh: Sheets, results: list[KotResult], label: str, dry: bool):
    sid, tab = config.SALES_DATA_SHEET_ID, config.KOT_DEST_TAB
    top, prev = find_block(sh, label)
    rows = (top, top + 1, top + 2)

    print(f"\nDEST    block rows {rows[0]}-{rows[2]}  (previous block: {prev!r})")

    # Never overwrite a filled block.
    existing = sh.read_range(sid, a1(tab, f"C{rows[0]}:K{rows[2]}"))
    if any(any(str(c).strip() for c in row) for row in existing):
        raise ScrapeError(
            f"{tab!r} rows {rows[0]}-{rows[2]} already contain data — refusing to overwrite. "
            "If this is a re-run, that date is already done."
        )

    by_id = {r.outlet_id: r for r in results}
    order = [oid for oid, _ in sorted(config.KOT_DEST_COL.items(),
                                      key=lambda kv: kv[1])]  # C,D,E... order

    total_row   = [config.KOT_DEST_METRIC_LABELS[0]] + [by_id[o].total_kot   for o in order] + [f"=SUM(C{rows[0]}:K{rows[0]})"]
    captain_row = [config.KOT_DEST_METRIC_LABELS[1]] + [by_id[o].captain_kot for o in order] + [f"=SUM(C{rows[1]}:K{rows[1]})"]
    pct_row     = [config.KOT_DEST_METRIC_LABELS[2]] + [by_id[o].captain_pct for o in order] + [f"=SUM(C{rows[2]}:K{rows[2]})"]

    if dry:
        print(f"  would write {tab!r}!A{rows[0]}   = {label}")
        print(f"  would write {tab!r}!B{rows[0]}:L{rows[2]}:")
        cols = "".join(f"{config.SHORT[o][:9]:>10}" for o in order)
        print(f"      {'':<16}{cols}{'Total':>10}")
        for nm, rw in (("Total KOT", total_row), ("Captain App KOT", captain_row), ("Captain App%", pct_row)):
            vals = "".join(f"{v:>10}" for v in rw[1:-1])
            print(f"      {nm:<16}{vals}{'  =SUM()':>10}")
        return

    sh.batch_write(sid, {
        a1(tab, f"A{rows[0]}"): [[label]],
        a1(tab, f"B{rows[0]}:L{rows[2]}"): [total_row, captain_row, pct_row],
    })

    back = sh.read_range(sid, a1(tab, f"C{rows[0]}:K{rows[1]}"))
    want_t = [by_id[o].total_kot for o in order]
    want_c = [by_id[o].captain_kot for o in order]
    if [int(x) for x in back[0]] != want_t or [int(x) for x in back[1]] != want_c:
        raise ScrapeError("destination readback mismatch — check the sheet")
    print(f"  wrote + verified B{rows[0]}:L{rows[2]}")


# ---------------------------------------------------------------------------
def selftest(pp: Petpooja):
    """Prove the HTTP client still matches values captured live on 14 Jul 2026."""
    st = config.SELFTEST
    bd = datetime.strptime(st["business_date"], "%Y-%m-%d").date()
    w = windows(bd)
    ok = True
    print(f"Self-test against known-good values for {st['business_date']}:\n")
    for oid, want in st["kot"].items():
        got = pp.kot_count(oid, w["kot_from"], w["kot_to"])
        mark = "OK  " if got == want else "FAIL"
        ok &= got == want
        print(f"  [{mark}] KOT     {config.SHORT[oid]:<20} expected {want}, got {got}")
    for oid, want in st["captain"].items():
        got = pp.captain_kots(oid, w["cap_from"], w["cap_to"])
        mark = "OK  " if got == want else "FAIL"
        ok &= got == want
        print(f"  [{mark}] Captain {config.SHORT[oid]:<20} expected {want}, got {got}")
    print("\n" + ("Client is healthy." if ok else
                  "Client is BROKEN — Petpooja likely changed a page. Do not trust writes."))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="pull and print, write nothing")
    ap.add_argument("--selftest", action="store_true", help="verify client against known values")
    ap.add_argument("--date", help="business day YYYY-MM-DD (default: yesterday IST)")
    args = ap.parse_args()

    try:
        pp = Petpooja.from_tokens()
    except SessionExpired as e:
        print(f"ERROR: {e}")
        return 2

    if args.selftest:
        return selftest(pp)

    bd = (datetime.strptime(args.date, "%Y-%m-%d").date() if args.date
          else (datetime.now(IST).date() - timedelta(days=1)))
    label = date_label(bd)

    print(f"Business day: {bd} ({label})")
    print(f"Mode: {'DRY RUN — nothing will be written' if args.dry_run else 'LIVE'}\n")

    try:
        results = pull(pp, bd)
    except (SessionExpired, ScrapeError) as e:
        print(f"\nERROR during Petpooja pull: {e}")
        return 2

    problems = sanity(results)
    if problems:
        print("\nSANITY CHECK FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 2

    tot_b = sum(r.total_kot for r in results)
    tot_c = sum(r.captain_kot for r in results)
    print(f"\n  {'TOTAL':<20} KOT {tot_b:>5}   Captain {tot_c:>5}   "
          f"{round(tot_c / tot_b * 100, 2) if tot_b else 0:>6.2f}%")

    sh = Sheets()
    try:
        source_plan(sh, results, label, args.dry_run)
        dest_plan(sh, results, label, args.dry_run)
    except ScrapeError as e:
        print(f"\nERROR: {e}")
        return 2

    if args.dry_run:
        print("\nDry run complete. Nothing was written.")
        print("Compare the numbers above with what the Claude task wrote this morning.")
    else:
        print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
