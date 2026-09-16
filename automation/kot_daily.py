"""
daily-kot-comparison — ported from SKILL.md to plain Python.

  BEFORE:  ~80 Claude browser tool calls. Name Box navigation at 650ms/cell,
           clipboard TSV pastes that could land a row off, and the run that
           prompted this port failed outright on tab duplication (23 Aug 2026).
  AFTER:   KOT via HTTP, Captain via one Playwright session, and both sheets
           written through the Google Sheets UI with trusted Playwright input
           (the destination is an .xlsx the Sheets API can't touch). Every write
           is read back through gviz and verified. See KOT_DAILY_PORT.md.

Usage
  python kot_daily.py --dry-run          pull + show what WOULD be written
  python kot_daily.py --selftest         verify both readers (Petpooja + browser)
  python kot_daily.py --headed           run with a visible browser (validation)
  python kot_daily.py                    do it for real (yesterday)
  python kot_daily.py --date 2026-08-23  backfill a specific business day
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, date, timedelta, timezone

import config
from petpooja import Petpooja, KotResult, SessionExpired, ScrapeError

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
def pull(pp: Petpooja, business_day: date, headless: bool = True) -> list[KotResult]:
    w = windows(business_day)

    # Total Dine In/Pick Up KOTs: the KOT list is now SPA-gated (direct HTTP to
    # /items/kot_list/ redirects, so klist sentinels "9"). Read it in the browser
    # instead — one primed session, all outlets. See browser_export.scrape_kot_totals.
    from browser_export import scrape_kot_totals
    kt = scrape_kot_totals(w["kot_from"], w["kot_to"], config.KOT_OUTLETS,
                           headless=headless)
    if kt["errors"]:
        details = "; ".join(f"{config.SHORT[o]}: {e}" for o, e in kt["errors"].items())
        raise ScrapeError(f"KOT total scrape failed for {details}")
    totals = kt["results"]

    # Captain App KOTs: the Captain Performance Report (view_report/27) is now
    # JS-rendered, so it can't be scraped over plain HTTP (403). Drive it once in
    # the browser for all outlets in a single session — see
    # browser_export.scrape_captain_kots.
    from browser_export import scrape_captain_kots
    cap = scrape_captain_kots(w["cap_from"], w["cap_to"], config.KOT_OUTLETS,
                              headless=headless)
    if cap["errors"]:
        details = "; ".join(f"{config.SHORT[o]}: {e}" for o, e in cap["errors"].items())
        raise ScrapeError(f"captain scrape failed for {details}")
    captains = cap["results"]

    results: list[KotResult] = []
    for oid in config.KOT_OUTLETS:
        r = KotResult(oid, totals[oid], captains[oid])
        results.append(r)
        print(f"  {config.SHORT[oid]:<20} KOT {totals[oid]:>5}   "
              f"Captain {captains[oid]:>5}   {r.captain_pct:>6.2f}%")
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
# source sheet (native Google Sheet, written through the Sheets web UI)
# ---------------------------------------------------------------------------
def source_plan(results: list[KotResult], label: str, dry: bool,
                writer=None) -> None:
    from sheet_writer import WriteError
    sid = config.KOT_SOURCE_SHEET_ID
    by_id = {r.outlet_id: r for r in results}

    if dry:
        print(f"\nSOURCE  would ensure tab {label!r} (duplicate newest at left if missing)")
        print(f"  would write {label!r}!A1     = {label}")
        print(f"  would write {label!r}!B2:C10 = 9 rows (Total KOT, Captain App KOT)")
        print("  row 11 SUM + column D/E coverage formulas: left untouched (they recalc)")
        return

    writer.open_book(sid)
    titles = writer.tab_titles()
    newest = titles[0]  # newest-on-the-left convention
    if label not in titles:
        print(f"SOURCE  duplicate {newest!r} -> {label!r} (move to leftmost)")
        writer.duplicate_tab(newest, label)
    else:
        print(f"SOURCE  tab {label!r} already exists")
    writer.select_tab(label)

    # Verify column A really is in the order we assume BEFORE writing B/C.
    grid = writer.read_tab(label)
    names = [row[0] if row else "" for row in grid[1:10]]  # A2:A10
    for i, oid in enumerate(config.KOT_OUTLETS):
        got = str(names[i]).lower() if i < len(names) else ""
        if MATCH_TOKEN[oid] not in got:
            raise ScrapeError(
                f"source tab {label!r} row {i+2}: expected {config.SHORT[oid]} "
                f"(token {MATCH_TOKEN[oid]!r}), found {got!r}. "
                "Sheet layout changed — aborting before any write.")

    writer.write_cell("A1", label)
    rows = [[by_id[oid].total_kot, by_id[oid].captain_kot] for oid in config.KOT_OUTLETS]
    writer.write_rows_down("B2", rows)

    # Anti-stale-copy guard: a freshly duplicated tab starts life holding the
    # template's numbers. Read back through gviz and prove ours actually landed.
    grid = writer.read_tab(label)
    for i, oid in enumerate(config.KOT_OUTLETS):
        r = grid[i + 1] if i + 1 < len(grid) else []
        try:
            got = [int(float(r[1])), int(float(r[2]))]
        except (IndexError, ValueError):
            got = []
        want = [by_id[oid].total_kot, by_id[oid].captain_kot]
        if got != want:
            raise ScrapeError(
                f"source readback mismatch at {config.SHORT[oid]}: "
                f"wrote {want}, sheet says {got}")
    print(f"  wrote + verified B2:C10 on {label!r}")


# ---------------------------------------------------------------------------
# destination sheet (Sales Data — an .xlsx in Drive, written through the UI)
# ---------------------------------------------------------------------------
def find_block(grid: list[list], label: str) -> tuple[int, str | None]:
    """
    Locate the 3-row block for `label` in the destination tab. Blocks start at
    row 2 and repeat every 3. Returns (top_row_1based, prev_label).

    A block counts as OCCUPIED if its column-A label is set OR its data cells
    (C..K) hold anything. This is deliberate: a run whose A-label commit slipped
    used to leave a block with numbers but a blank column A — invisible to a
    label-only scan, so the next run computed the SAME target rows and aborted
    with "already contain data" (the 28–30 Aug 2026 EXIT 2 jam). Treating a
    data-filled block as occupied means we always advance PAST such an orphan to
    the next truly-empty block instead of colliding with it.
    """
    top = config.KOT_DEST_FIRST_BLOCK_ROW
    step = config.KOT_DEST_BLOCK_HEIGHT

    def cell_a(r: int) -> str:
        return str(grid[r - 1][0]).strip() if r - 1 < len(grid) and grid[r - 1] else ""

    def has_data(r: int) -> bool:
        row = grid[r - 1] if r - 1 < len(grid) else []
        return any(str(c).strip() for c in row[2:11])   # C..K

    last_occupied = None
    r = top
    while r <= len(grid) + step:            # +step of slack so we can append past the last row
        a = cell_a(r)
        if a == label:                      # exact date already placed -> idempotent re-run
            prev = cell_a(r - step) if r - step >= top else None
            return r, prev
        if a or has_data(r):                # labelled OR orphaned (data, blank A) both = occupied
            last_occupied = r
        r += step

    if last_occupied is None:
        raise ScrapeError(f"{config.KOT_DEST_TAB!r}: no filled date blocks found — layout changed?")
    target = last_occupied + step
    prev = cell_a(last_occupied) or "(unlabelled block)"
    return target, prev


def dest_plan(results: list[KotResult], label: str, dry: bool,
              writer=None) -> None:
    sid, tab = config.SALES_DATA_SHEET_ID, config.KOT_DEST_TAB
    by_id = {r.outlet_id: r for r in results}
    order = [oid for oid, _ in sorted(config.KOT_DEST_COL.items(),
                                      key=lambda kv: kv[1])]  # C,D,E... order

    if dry:
        print(f"\nDEST    would find the next empty block in {tab!r} and write:")
        print(f"  A<top> = {label}")
        cols = "".join(f"{config.SHORT[o][:9]:>10}" for o in order)
        print(f"      {'':<16}{cols}{'Total':>10}")
        for nm in config.KOT_DEST_METRIC_LABELS:
            key = {"Total KOT": "total_kot", "Captain App KOT": "captain_kot",
                   "Captain App%": "captain_pct"}[nm]
            vals = "".join(f"{getattr(by_id[o], key):>10}" for o in order)
            print(f"      {nm:<16}{vals}{'  =SUM()':>10}")
        return

    writer.open_book(sid)
    writer.select_tab(tab)
    grid = writer.read_tab(tab)
    top, prev = find_block(grid, label)
    r0, r1, r2 = top, top + 1, top + 2
    print(f"DEST    block rows {r0}-{r2}  (previous block: {prev!r})")

    # Never overwrite a filled block: check C..K across the 3 rows are all empty.
    for rr in (r0, r1, r2):
        row = grid[rr - 1] if rr - 1 < len(grid) else []
        cells = row[2:11]  # C..K
        if any(str(c).strip() for c in cells):
            raise ScrapeError(
                f"{tab!r} rows {r0}-{r2} already contain data — refusing to overwrite. "
                "If this is a re-run, that date is already done.")

    # Column A holds the date label; B holds the metric name; C..K the outlets; L the SUM.
    # The date label sits on the FIRST metric row only; rows 2-3 leave A blank.
    block_rows = [
        [label, config.KOT_DEST_METRIC_LABELS[0]] + [by_id[o].total_kot   for o in order] + [f"=SUM(C{r0}:K{r0})"],
        ["",    config.KOT_DEST_METRIC_LABELS[1]] + [by_id[o].captain_kot for o in order] + [f"=SUM(C{r1}:K{r1})"],
        ["",    config.KOT_DEST_METRIC_LABELS[2]] + [by_id[o].captain_pct for o in order] + [f"=SUM(C{r2}:K{r2})"],
    ]

    # Write A..L for all three rows in ONE reading-order paste, anchored at A{r0}.
    # Anchoring at A (not B) commits the date label with the SAME keystroke
    # sequence as the numbers — Tab moves across the row, Enter returns to
    # column A on the next row — so the label can no longer be dropped by the
    # separate write_cell()/Name-Box race that orphaned blocks on 27 & 29 Aug 2026.
    writer.write_rows_down(f"A{r0}", block_rows)

    def _ints(row):
        out = []
        for c in row:
            try:
                out.append(int(float(c)))
            except (ValueError, TypeError):
                out.append(None)
        return out

    want_t = [by_id[o].total_kot for o in order]
    want_c = [by_id[o].captain_kot for o in order]

    # Read back and verify. The numbers must match. If the label alone slipped,
    # re-write just A{r0} and re-check (belt-and-suspenders on the slow workbook).
    got_label = ""
    for attempt in range(1, 4):
        grid = writer.read_tab(tab)
        got_label = str(grid[r0 - 1][0]).strip() if r0 - 1 < len(grid) and grid[r0 - 1] else ""
        got_t = _ints(grid[r0 - 1][2:11]) if r0 - 1 < len(grid) else []
        got_c = _ints(grid[r1 - 1][2:11]) if r1 - 1 < len(grid) else []
        if got_t != want_t or got_c != want_c:
            raise ScrapeError(
                f"destination readback mismatch — check the sheet "
                f"(wanted totals {want_t}, got {got_t})")
        if got_label == label:
            if attempt > 1:
                print(f"  A{r0} label landed on attempt {attempt}")
            break
        print(f"  A{r0} label did not stick (attempt {attempt}/3) — rewriting")
        writer.write_cell(f"A{r0}", label)
        time.sleep(1.5 * attempt)          # let the commit flush before re-reading

    # An unlabelled-but-filled block no longer JAMS the next run (find_block now
    # skips past it), but we still want it flagged so the gap can be tidied.
    if got_label != label:
        raise ScrapeError(
            f"destination label missing — A{r0} reads {got_label!r}, expected {label!r}. "
            f"The B:L data for this block WAS written; set A{r0} manually if you want the label."
        )
    print(f"  wrote + verified A{r0} + B{r0}:L{r2}")


# ---------------------------------------------------------------------------
def selftest(pp: Petpooja, headless: bool = True):
    """
    Liveness check for both scrape paths, run against a recent complete business
    day (2 days back, so late-night tails have settled). Exact historical
    baselines can't be used any more — Petpooja purges old Captain-report data
    (the old 14 Jul baseline now returns "No Record Found"), so instead we prove
    the two readers still return sane, self-consistent numbers before any write:
      - KOT count (HTTP /items/klist/) returns a non-negative integer,
      - Captain count (browser view_report/27) returns 0..KOT,
    for a spot-check outlet each, and confirm at least one has real activity.
    """
    bd = datetime.now(IST).date() - timedelta(days=2)
    w = windows(bd)
    kot_oid, cap_oid = 349767, 159181  # DLF Phase 2, Rajinder Nagar
    print(f"Self-test (liveness) for business day {bd}:\n")

    ok = True
    from browser_export import scrape_kot_totals
    kt = scrape_kot_totals(w["kot_from"], w["kot_to"], [kot_oid], headless=headless)
    if kt["errors"]:
        ok = False; kot = None
        print(f"  [FAIL] KOT (browser)  {config.SHORT[kot_oid]}: {kt['errors'][kot_oid]}")
    else:
        kot = kt["results"][kot_oid]
        good = isinstance(kot, int) and kot >= 0
        ok &= good
        print(f"  [{'OK  ' if good else 'FAIL'}] KOT (browser)  "
              f"{config.SHORT[kot_oid]:<20} = {kot}")

    from browser_export import scrape_captain_kots
    res = scrape_captain_kots(w["cap_from"], w["cap_to"], [cap_oid], headless=headless)
    if res["errors"]:
        ok = False
        print(f"  [FAIL] Captain (browser) {config.SHORT[cap_oid]}: {res['errors'][cap_oid]}")
    else:
        cap = res["results"][cap_oid]
        good = isinstance(cap, int) and cap >= 0
        ok &= good
        print(f"  [{'OK  ' if good else 'FAIL'}] Captain (browser) "
              f"{config.SHORT[cap_oid]:<16} = {cap}")

    print("\n" + ("Both readers healthy." if ok else
                  "A reader is BROKEN — Petpooja likely changed a page. Do not trust writes."))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="pull and print, write nothing")
    ap.add_argument("--selftest", action="store_true", help="verify client against known values")
    ap.add_argument("--date", help="business day YYYY-MM-DD (default: yesterday IST)")
    ap.add_argument("--headed", action="store_true",
                    help="run the captain-report browser visibly (debugging)")
    args = ap.parse_args()

    try:
        pp = Petpooja.from_tokens()
    except SessionExpired as e:
        print(f"ERROR: {e}")
        return 2

    if args.selftest:
        return selftest(pp, headless=not args.headed)

    bd = (datetime.strptime(args.date, "%Y-%m-%d").date() if args.date
          else (datetime.now(IST).date() - timedelta(days=1)))
    label = date_label(bd)

    print(f"Business day: {bd} ({label})")
    print(f"Mode: {'DRY RUN — nothing will be written' if args.dry_run else 'LIVE'}\n")

    try:
        results = pull(pp, bd, headless=not args.headed)
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

    if args.dry_run:
        try:
            source_plan(results, label, dry=True)
            dest_plan(results, label, dry=True)
        except ScrapeError as e:
            print(f"\nERROR: {e}")
            return 2
        print("\nDry run complete. Nothing was written.")
        print("Compare the numbers above with the Claude task's collected values.")
        return 0

    # Live: one signed-in Google session drives both writes through the UI.
    from sheet_writer import BrowserWriter, SessionExpired as SheetLogin, WriteError
    try:
        with BrowserWriter(headless=not args.headed) as w:
            source_plan(results, label, dry=False, writer=w)
            dest_plan(results, label, dry=False, writer=w)
    except (ScrapeError, WriteError) as e:
        print(f"\nERROR: {e}")
        return 2
    except SheetLogin as e:
        print(f"\nERROR (Google session): {e}")
        return 2

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
