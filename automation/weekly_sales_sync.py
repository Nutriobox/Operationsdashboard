"""
Petpooja Weekly Sales Sync — Playwright/HTTP port of the Claude
"petpooja-weekly-sales-sync" task.

WHAT IT DOES
  Pulls last completed Mon-Sun week's per-outlet **Total Sales** from Petpooja's
  "All Restaurant Sales Report" (view_report/9) over HTTP (tokens.json session),
  then writes each outlet's rounded integer into the active Weekly tab of the
  Sales Data Google Sheet through the signed-in browser profile, plus the
  consolidated sum in row 3.

  Same building blocks as the KOT ports: Petpooja over HTTP (petpooja.py), the
  sheet write + read-back through the browser (sheet_writer.BrowserWriter).

SAFETY (why this can run unattended)
  It refuses to write unless EVERY guard passes:
    - all 10 outlets are matched in the report table (no missing/extra),
    - the 10 rounded outlet totals reconcile with the report Total row (+/-2),
    - the target column's row-2 header equals the target Monday's day-of-month,
    - every target cell is empty before writing.
  Any failure aborts with a clear message and writes nothing.

USAGE
  python weekly_sales_sync.py --selftest              readers live, write nothing
  python weekly_sales_sync.py --dry-run               pull + show what WOULD be written
  python weekly_sales_sync.py --dry-run --monday 2026-08-24
  python weekly_sales_sync.py --headed                run with a visible browser
  python weekly_sales_sync.py                         LIVE (last completed week)

VALIDATE BEFORE SCHEDULING (cannot be tested off the laptop):
  1) Confirm view_report/9 returns ALL outlet rows in one call. If it filters to
     a single outlet, set PULL_PER_OUTLET = True below.
  2) Confirm the report's outlet labels match OUTLET_ALIASES (adjust if Petpooja
     shows different names).
  3) Confirm the Total Sales date boundary (00:00->23:59 vs a 01:00 business day).
"""
import argparse
import re
import sys
from datetime import date, datetime, timedelta

import config
from petpooja import Petpooja, ScrapeError

try:
    import kot_common as kc          # only for kc.IST if present; optional
    IST = getattr(kc, "IST", None)
except Exception:
    IST = None

# --- If the All-Restaurant report ever filters to one outlet, flip this True ---
PULL_PER_OUTLET = False

SALES_SHEET_ID = config.SALES_DATA_SHEET_ID

# Outlet_id -> (sheet row, aliases seen in the Petpooja report). Row numbers and
# the Petpooja short labels are from the task's confirmed mapping.
OUTLET_ROW = {
    9960:   (7,  ["rohini", "prashant vihar", "prashant"]),
    19652:  (11, ["jp", "janakpuri"]),
    16011:  (15, ["kkd", "karkardooma"]),
    62697:  (19, ["dwarka"]),
    62695:  (23, ["shivalik"]),
    80991:  (27, ["advant", "noida"]),
    159181: (31, ["rn", "rajinder nagar", "rajinder"]),
    349767: (35, ["dlf", "dlf phase 2"]),
    369621: (39, ["sec 15", "sector 15", "gurugram"]),
    136183: (43, ["cloud", "sector 63 noida", "sector 63", "sec 63"]),
}
CONSOLIDATED_ROW = 3
ANCHOR_COL_INDEX = 105          # column DA (1-indexed)
ANCHOR_DATE = date(2026, 1, 5)  # DA == Mon 5 Jan 2026
WEEKLY_TAB_RANGE = range(20, 60)   # "Weekly NN" candidates to scan for --auto-tab


# --------------------------------------------------------------------------- #
def col_to_a1(idx: int) -> str:
    """1-indexed column number -> A1 letters (105 -> 'DA')."""
    s = ""
    while idx > 0:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def target_week(ref: date) -> tuple[date, date]:
    """Return (Monday, Sunday) of the last completed week before `ref`."""
    this_monday = ref - timedelta(days=ref.weekday())
    mon = this_monday - timedelta(days=7)
    return mon, mon + timedelta(days=6)


def target_column(monday: date) -> str:
    return col_to_a1(ANCHOR_COL_INDEX + (monday - ANCHOR_DATE).days)


def _num(txt) -> float:
    return float(re.sub(r"[^\d.\-]", "", str(txt)) or 0)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", str(s).lower()).strip()


def _match_outlet(label: str) -> int | None:
    """Match by the LONGEST alias contained in the label — so specific names win
    over generic ones (e.g. "sector 63 noida" beats the bare "noida" that also
    tags the Advant outlet). Without this, both Noida outlets collide on "noida"."""
    n = _norm(label)
    if not n:
        return None
    best_oid, best_len = None, 0
    for oid, (_row, aliases) in OUTLET_ROW.items():
        for a in aliases:
            if a and a in n and len(a) > best_len:
                best_oid, best_len = oid, len(a)
    return best_oid


# --------------------------------------------------------------------------- #
def parse_sales_table(soup) -> tuple[dict[int, float], float | None]:
    """
    From an All-Restaurant-Sales report soup, return
    ({outlet_id: total_sales_float}, report_total_or_None).
    Finds the table with a 'Total Sales' header; matches each row's first text
    cell to an outlet; reads the Total Sales column by HEADER TEXT (not index).
    """
    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        ts_idx = next(
            (i for i, h in enumerate(headers)
             if re.search(r"total\s*sales", h, re.I) and not re.search(r"net", h, re.I)),
            None,
        )
        if ts_idx is None:
            continue
        found: dict[int, float] = {}
        report_total = None
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) <= ts_idx:
                continue
            label = cells[0].get_text(" ", strip=True)
            val = _num(cells[ts_idx].get_text(strip=True))
            if re.search(r"\btotal\b", label, re.I) and _match_outlet(label) is None:
                report_total = val
                continue
            oid = _match_outlet(label)
            if oid is not None and oid not in found:
                found[oid] = val
        if found:
            return found, report_total
    raise ScrapeError("All-Restaurant-Sales: no table with a 'Total Sales' header found.")


def pull_week_sales(pp: Petpooja, monday: date, sunday: date,
                    headless: bool = True) -> tuple[dict[int, int], float | None]:
    frm = f"{monday.isoformat()} 00:00:00"
    to = f"{sunday.isoformat()} 23:59:59"
    # The pure-HTTP custom_report is gated/unreliable from the laptop (view_report/9
    # returns no form). Read it through the primed single-outlet browser session,
    # same fix as KOT/Captain. See browser_export.browser_custom_report.
    from bs4 import BeautifulSoup
    from browser_export import browser_custom_report

    def _report(oid):
        html = browser_custom_report(config.REPORT_ALL_RESTAURANT_SALES, oid, frm, to,
                                     headless=headless)
        return BeautifulSoup(html, "html.parser")

    if PULL_PER_OUTLET:
        totals, report_total = {}, 0.0
        for oid in OUTLET_ROW:
            one, _ = parse_sales_table(_report(oid))
            totals[oid] = one.get(oid, 0.0)
        report_total = None
    else:
        anchor_oid = next(iter(OUTLET_ROW))
        totals, report_total = parse_sales_table(_report(anchor_oid))
    rounded = {oid: int(round(v)) for oid, v in totals.items()}
    return rounded, report_total


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="pull and print, write nothing")
    ap.add_argument("--selftest", action="store_true", help="verify the reader is live")
    ap.add_argument("--monday", help="target week's Monday YYYY-MM-DD (default: last completed week)")
    ap.add_argument("--tab", help='Weekly tab to write, e.g. "Weekly 27" (required for a live write)')
    ap.add_argument("--auto-tab", action="store_true",
                    help='auto-pick the Weekly tab whose row-2 matches the target Monday')
    ap.add_argument("--headed", action="store_true", help="visible browser for the sheet write")
    args = ap.parse_args()

    pp = Petpooja.from_tokens()

    if args.selftest:
        mon, sun = target_week(date.today())
        got, rep = pull_week_sales(pp, mon, sun, headless=not args.headed)
        print(f"selftest OK — {len(got)}/10 outlets, week {mon}..{sun}, report_total={rep}")
        return 0 if len(got) == len(OUTLET_ROW) else 1

    if args.monday:
        mon = datetime.strptime(args.monday, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            print(f"ERROR: --monday {args.monday} is a {mon.strftime('%A')}, not a Monday.")
            return 2
        sun = mon + timedelta(days=6)
    else:
        mon, sun = target_week(date.today())

    col = target_column(mon)
    print(f"Target week: {mon} .. {sun}  ->  column {col}")

    rounded, report_total = pull_week_sales(pp, mon, sun, headless=not args.headed)

    # Guard 1: every outlet present.
    missing = [config.SHORT[o] for o in OUTLET_ROW if o not in rounded]
    if missing:
        print(f"ABORT: missing outlets in report: {missing}. "
              "If view_report/9 filters to one outlet, set PULL_PER_OUTLET=True.")
        return 3

    consolidated = sum(rounded.values())

    # Guard 2: reconcile with the report Total row (if the report exposed one).
    if report_total is not None and abs(consolidated - round(report_total)) > 2:
        print(f"ABORT: outlet sum {consolidated} != report Total {round(report_total)} (>2).")
        return 4

    print(f"{'OUTLET':<22}{'ROW':>5}{'TOTAL SALES':>14}")
    for oid, (row, _a) in OUTLET_ROW.items():
        print(f"{config.SHORT[oid]:<22}{row:>5}{rounded[oid]:>14,}")
    print(f"{'CONSOLIDATED':<22}{CONSOLIDATED_ROW:>5}{consolidated:>14,}")

    if args.dry_run:
        print("\nDRY RUN — nothing written.")
        return 0

    if not args.tab and not args.auto_tab:
        print('ABORT: a live write needs --tab "Weekly NN" (the active weekly tab) '
              "or --auto-tab. Re-run with one of them.")
        return 7

    ci = ANCHOR_COL_INDEX + (mon - ANCHOR_DATE).days - 1   # 0-indexed grid column

    def cell(grid, row):
        return str(grid[row - 1][ci]).strip() if (
            grid and row - 1 < len(grid) and ci < len(grid[row - 1])) else ""

    def resolve_tab(writer) -> str | None:
        """Scan 'Weekly NN' tabs for the one whose row-2 == target Monday's day
        and whose consolidated cell is still empty."""
        want = str(mon.day)
        for n in WEEKLY_TAB_RANGE:
            name = f"Weekly {n}"
            try:
                g = writer.read_tab(name)
            except Exception:
                continue
            if cell(g, 2) in (want, want + ".0") and not cell(g, CONSOLIDATED_ROW):
                return name
        return None

    # ---- LIVE write through the signed-in browser profile --------------------
    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=not args.headed) as writer:
        writer.open_book(SALES_SHEET_ID)
        tab = args.tab or resolve_tab(writer)
        if not tab:
            print("ABORT: could not resolve the Weekly tab automatically. "
                  'Re-run with --tab "Weekly NN".')
            return 7
        print(f"Weekly tab: {tab}")
        writer.select_tab(tab)
        grid = writer.read_tab(tab)

        # Guard 3: the target column's row-2 header must equal the Monday's day.
        want_day, got_day = str(mon.day), cell(grid, 2)
        if got_day not in (want_day, want_day + ".0"):
            print(f"ABORT: {col}2 on {tab!r} reads {got_day!r}, expected day {want_day!r} "
                  f"for {mon}. Wrong tab or wrong column — not writing.")
            return 5

        # Guard 4: never overwrite.
        for oid, (row, _a) in OUTLET_ROW.items():
            if cell(grid, row):
                print(f"ABORT: {col}{row} ({config.SHORT[oid]}) on {tab!r} already has "
                      f"{cell(grid, row)!r} — not writing.")
                return 6
        if cell(grid, CONSOLIDATED_ROW):
            print(f"ABORT: {col}{CONSOLIDATED_ROW} (consolidated) already filled — not writing.")
            return 6

        # Write each outlet, consolidated last.
        for oid, (row, _a) in OUTLET_ROW.items():
            writer.write_cell(f"{col}{row}", rounded[oid])
        writer.write_cell(f"{col}{CONSOLIDATED_ROW}", consolidated)

        # Guard 5: read back a sample and verify.
        grid = writer.read_tab(tab)
        checks = [(CONSOLIDATED_ROW, consolidated),
                  (OUTLET_ROW[9960][0], rounded[9960]),
                  (OUTLET_ROW[136183][0], rounded[136183])]
        for row, want in checks:
            have = cell(grid, row)
            if _num(have) != want:
                raise ScrapeError(f"readback mismatch at {col}{row}: wrote {want}, read {have!r}")

    print(f"\nWrote + verified week {mon}..{sun} into {tab!r} column {col} "
          f"(consolidated {consolidated:,}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
