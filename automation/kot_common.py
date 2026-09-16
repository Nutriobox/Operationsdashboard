"""
Shared building blocks for the KOT-comparison ports.

`kot_daily.py` was the first port (daily source sheet + "Sales Data" mirror) and
keeps its own copy of this logic so it stays a single readable file. The weekly
(`kot_weekly.py`) and monthly (`kot_monthly.py`) ports are pure "source-only"
jobs — one tab per period, no destination mirror — so they share the pull /
sanity / source-write logic here to avoid three near-identical copies.

The write technique is exactly the daily one: pull KOT over HTTP and Captain via
one Playwright browser session, then create/fill the period tab through the
signed-in Google Sheets web UI (trusted keyboard input), reading every write back
through gviz before trusting it. See KOT_DAILY_PORT.md for the full rationale.
"""
from __future__ import annotations

from datetime import timedelta, timezone

import config
from petpooja import Petpooja, KotResult, ScrapeError

IST = timezone(timedelta(hours=5, minutes=30))

# Distinctive token per outlet, used to verify the tab's column A really is in
# the order we assume BEFORE writing anything into B/C. Same layout (rows 2-10)
# in the daily, weekly and monthly source sheets.
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


# ---------------------------------------------------------------------------
# pull  (KOT via HTTP, Captain via one browser session)
# ---------------------------------------------------------------------------
def pull(pp: Petpooja, kot_from: str, kot_to: str,
         cap_from: str, cap_to: str, headless: bool = True) -> list[KotResult]:
    """
    Pull Total (Dine In + Pick Up) KOT and Captain App KOT for all 9 KOT outlets
    over an arbitrary window. `kot_*` use Petpooja's KOT format
    ("15 Jun 2026 13:00:00"); `cap_*` use the report format
    ("2026-06-15 13:00:00").
    """
    # Total (Dine In + Pick Up) KOT: the KOT list is now SPA-gated, so the old
    # pure-HTTP pp.kot_count sentinels "9". Read it in the browser instead — one
    # primed session for all outlets. See browser_export.scrape_kot_totals.
    from browser_export import scrape_kot_totals
    kt = scrape_kot_totals(kot_from, kot_to, config.KOT_OUTLETS, headless=headless)
    if kt["errors"]:
        details = "; ".join(f"{config.SHORT[o]}: {e}" for o, e in kt["errors"].items())
        raise ScrapeError(f"KOT total scrape failed for {details}")
    totals = kt["results"]

    # view_report/27 is JS-rendered (403 to a direct POST), so Captain numbers
    # come from one Playwright session for all outlets — same as the daily port.
    from browser_export import scrape_captain_kots
    cap = scrape_captain_kots(cap_from, cap_to, config.KOT_OUTLETS, headless=headless)
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
                f"({r.total_kot}) — impossible, refusing to write")
        if r.total_kot == 0:
            problems.append(f"{config.SHORT[r.outlet_id]}: zero KOTs — check the outlet")
        # Added 2026-08-27. The monthly validation returned Captain=0 for
        # Rajinder Nagar (truth: 1505) and passed every gate, because only
        # total_kot was checked for zero. A Captain read of exactly 0 against a
        # non-trivial KOT count is a scrape failure, not a business fact.
        if r.captain_kot == 0 and r.total_kot > 20:
            problems.append(
                f"{config.SHORT[r.outlet_id]}: Captain App KOT is 0 against "
                f"{r.total_kot} KOTs — treating as a failed read, refusing to write")
    return problems


def coverage_warnings(results: list[KotResult], floor: float = 60.0) -> list[str]:
    """
    Non-fatal warnings for implausibly low Captain coverage.

    Separate from sanity() because low coverage CAN be genuine (Noida really does
    sit near 45%). These are printed so a partial read is visible to a human even
    when it clears the hard gates — the monthly Captain reader under-reports on
    long windows and this is the symptom to watch for.
    """
    warns = []
    for r in results:
        if r.total_kot > 0 and r.captain_pct < floor:
            warns.append(
                f"{config.SHORT[r.outlet_id]}: Captain coverage "
                f"{r.captain_pct:.1f}% (< {floor:.0f}%) — verify before trusting")
    return warns


def print_totals(results: list[KotResult]) -> None:
    tot_b = sum(r.total_kot for r in results)
    tot_c = sum(r.captain_kot for r in results)
    pct = round(tot_c / tot_b * 100, 2) if tot_b else 0
    print(f"\n  {'TOTAL':<20} KOT {tot_b:>5}   Captain {tot_c:>5}   {pct:>6.2f}%")


# ---------------------------------------------------------------------------
# source write  (native Google Sheet, written through the Sheets web UI)
# ---------------------------------------------------------------------------
def write_source(results: list[KotResult], sheet_id: str, label: str,
                 dry: bool, writer=None, *, write_a1: bool = False) -> None:
    """
    Ensure the period tab `label` exists (duplicate the newest/leftmost tab if
    not, keeping newest-on-the-left) and write B2:C10 = (Total KOT, Captain KOT)
    for the 9 outlets. D (coverage) and row 11 (TOTAL) are formulas that recalc.

    `write_a1` is False for the weekly/monthly sheets (A1 is an "Outlets" header
    — never touched). The daily sheet, which keeps its date in A1, is handled by
    kot_daily.py's own copy of this routine.

    Every write is read back through gviz and compared; any mismatch raises.
    """
    by_id = {r.outlet_id: r for r in results}

    if dry:
        print(f"\nSOURCE  would ensure tab {label!r} (duplicate newest at left if missing)")
        if write_a1:
            print(f"  would write {label!r}!A1     = {label}")
        print(f"  would write {label!r}!B2:C10 = 9 rows (Total KOT, Captain App KOT)")
        print("  column D coverage + row 11 SUM: left untouched (they recalc)")
        return

    writer.open_book(sheet_id)
    titles = writer.tab_titles()
    newest = titles[0]  # newest-on-the-left convention
    if label not in titles:
        print(f"SOURCE  duplicate {newest!r} -> {label!r} (move to leftmost)")
        writer.duplicate_tab(newest, label)
    else:
        print(f"SOURCE  tab {label!r} already exists — filling in place")
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

    if write_a1:
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
# liveness self-test  (both readers, one spot-check outlet each)
# ---------------------------------------------------------------------------
def liveness(pp: Petpooja, kot_from: str, kot_to: str,
             cap_from: str, cap_to: str, headless: bool = True) -> int:
    """
    Prove both scrape paths still return sane numbers for the given window,
    without writing anything. KOT via HTTP for DLF Phase 2, Captain via browser
    for Rajinder Nagar. Returns 0 if healthy, 1 if a reader is broken.
    """
    kot_oid, cap_oid = 349767, 159181
    print(f"Self-test (liveness) for window {kot_from} -> {kot_to}:\n")

    ok = True
    from browser_export import scrape_kot_totals
    kt = scrape_kot_totals(kot_from, kot_to, [kot_oid], headless=headless)
    if kt["errors"]:
        ok = False
        print(f"  [FAIL] KOT (browser)  {config.SHORT[kot_oid]}: {kt['errors'][kot_oid]}")
    else:
        kot = kt["results"][kot_oid]
        good = isinstance(kot, int) and kot >= 0
        ok &= good
        print(f"  [{'OK  ' if good else 'FAIL'}] KOT (browser)  "
              f"{config.SHORT[kot_oid]:<20} = {kot}")

    from browser_export import scrape_captain_kots
    res = scrape_captain_kots(cap_from, cap_to, [cap_oid], headless=headless)
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
