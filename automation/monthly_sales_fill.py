"""
Monthly Sales Fill -> Playwright (port of the Cowork task
`nutriobox-weekly-petpooja-sales-fill`). Runs every Monday morning.

For each outlet, pull month-to-date Total Sales (1st of the current month .. yesterday)
from Petpooja's dashboard JSON, write it into the current month's "Sale" column of the
"Monthly" tab of the Sales sheet, and set Avg/day = Sale / N (N = day-of-month of
yesterday). It also fills the small red month-over-month GROWTH cells in the even rows
of the Avg/day column (row r+1 for each data row r), matching the sheet's existing
pattern: =(<avg>r - <prevAvg>r)/<prevAvg>r%  (current month's Avg/day vs the previous
month's Avg/day, 2 columns to the left, as a percent). No Claude tokens.

    python monthly_sales_fill.py --selftest            # pull + locate column, write nothing
    python monthly_sales_fill.py --dry-run             # + preview every cell, write nothing
    python monthly_sales_fill.py --dry-run --date 2026-09-04
    python monthly_sales_fill.py --headed              # live, visible browser
    python monthly_sales_fill.py                       # live (scheduled mode)

Safety: if the current month's column does not exist yet, it STOPS and reports (the
user inserts each new month's 2 columns manually, before the summary block) — it never
creates a column or writes, to avoid clobbering the adjacent cumulative-summary block.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta, timezone

import config

IST = timezone(timedelta(hours=5, minutes=30))
SHEET_ID = "1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs"
TAB = "Monthly"

# res_id -> sheet row in the Monthly tab (Sale value goes here; Avg/day in same row).
RES_ROW = {
    9960: 5,    # Prashant Vihar / Rohini
    19652: 7,   # Janakpuri
    16011: 9,   # Karkardooma
    62697: 11,  # Dwarka
    62695: 13,  # Shivalik
    80991: 15,  # Noida / Advant
    159181: 17, # Rajinder Nagar
    349767: 19, # DLF Phase 2
    369621: 21, # Sector 15, Gurugram
    136183: 23, # Sector 63 Noida
}
TOTAL_ROW = 3   # company Total Sales (static value, not a formula)

_MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"])}


def col_a1(idx1: int) -> str:
    """1-indexed column number -> A1 letters (27 -> 'AA')."""
    s = ""
    while idx1 > 0:
        idx1, r = divmod(idx1 - 1, 26)
        s = chr(65 + r) + s
    return s


def parse_month_header(text: str):
    """Return (year, month) for a single-month header, or None (summary/empty/range)."""
    t = (text or "").strip()
    if not t:
        return None
    # A summary-range header ("June 25 - Mar 26") won't match any single-month
    # pattern below, so it falls through to None on its own.
    m = re.match(r"^([A-Za-z]{3,9})\s+(\d{2,4})$", t)          # "June 26" / "June 2026"
    if m and m.group(1).lower() in _MONTHS:
        y = int(m.group(2)); y += 2000 if y < 100 else 0
        return (y, _MONTHS[m.group(1).lower()])
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", t)          # m/d/Y
    if m:
        return (int(m.group(3)), int(m.group(1)))
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", t)              # Y-m-d
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return None


def find_month_block(row1: list[str], want_year: int, want_month: int):
    """Return the 0-based column index of the current month's Sale header, or None."""
    for j, cell in enumerate(row1):
        ym = parse_month_header(cell)
        if ym == (want_year, want_month):
            return j
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="pull + locate, write nothing")
    ap.add_argument("--selftest", action="store_true", help="pull + locate column, no sheet write")
    ap.add_argument("--date", help="override to_date YYYY-MM-DD (default: yesterday IST)")
    ap.add_argument("--headed", action="store_true", help="visible browser")
    args = ap.parse_args()
    headless = not args.headed

    to_date = (datetime.strptime(args.date, "%Y-%m-%d").date() if args.date
               else datetime.now(IST).date() - timedelta(days=1))
    from_date = to_date.replace(day=1)
    N = to_date.day
    print(f"period      : {from_date} .. {to_date}  (N={N} days)")

    # ---- pull ----
    from browser_export import fetch_restaurant_sales
    data = fetch_restaurant_sales(from_date.isoformat(), to_date.isoformat(), headless=headless)
    by_res, total = data["by_res"], data["total"]
    print(f"outlets     : {len(by_res)}  total(API)={total}")

    missing = [config.SHORT.get(r, r) for r in RES_ROW if r not in by_res]
    if missing:
        print(f"ABORT: outlets missing from API: {missing}")
        return 3
    s = sum(by_res[r] for r in RES_ROW)
    if total is not None and abs(s - total) > 1:
        print(f"ABORT: outlet sum {s} != API total {total} (diff {s-total})")
        return 3
    print(f"sum check   : outlets sum {s} == total {total}  OK")

    # ---- locate the current month's column ----
    from sheet_writer import BrowserWriter, WriteError, SessionExpired as SheetLogin
    with BrowserWriter(headless=headless) as w:
        w.open_book(SHEET_ID)
        grid = w.read_tab(TAB)
        row1 = grid[0] if grid else []
        row2 = grid[1] if len(grid) > 1 else []
        j = find_month_block(row1, to_date.year, to_date.month)
        if j is None:
            want = to_date.strftime("%B %Y")
            print(f"STOP: no column for {want} in the Monthly tab — it must be added "
                  "manually (insert the 2 month columns before the summary block). "
                  "Nothing written.")
            return 1
        sale_col = col_a1(j + 1)
        avg_col = col_a1(j + 2)
        # Previous month's Avg/day column sits 2 columns to the left of avg_col.
        # (Its 1-indexed column number equals j, the 0-based index of this month's
        # Sale header.) Only use it if the block to the left is really a month — the
        # growth cells compare this month's Avg/day against it.
        prev_avg_col = (col_a1(j) if j >= 2 and parse_month_header(row1[j - 2])
                        else None)
        print(f"prev month  : {'Avg col ' + prev_avg_col if prev_avg_col else 'none (no growth cells will be written)'}")
        # sanity: row 2 should label these Sale / Avg
        lbl_sale = (row2[j] if j < len(row2) else "").strip().lower()
        lbl_avg = (row2[j + 1] if j + 1 < len(row2) else "").strip().lower()
        print(f"month block : header {row1[j]!r} -> Sale col {sale_col}, Avg col {avg_col} "
              f"(row2 labels: {row2[j] if j < len(row2) else ''!r}/"
              f"{row2[j+1] if j+1 < len(row2) else ''!r})")
        # Confirm block orientation. The month header already can't be the summary
        # block (its range header doesn't parse), so requiring the "Avg/day" label
        # on the RIGHT column is enough — the newest month's "Sale" label cell is
        # sometimes blank/merged, which is fine.
        if "avg" not in lbl_avg and "sale" not in lbl_sale:
            print("ABORT: neither a 'Sale' nor an 'Avg/day' label under the located "
                  "header — refusing to write into the wrong block.")
            return 3

        # ---- build the write plan ----
        # (row, sale_value, avg_formula, growth_cell, growth_formula)
        def growth_for(row):
            """MoM growth cell (even row r+1) + formula, matching the sheet pattern
            =(<avg>r - <prevAvg>r)/<prevAvg>r% — or (None, None) if no prior month."""
            if not prev_avg_col:
                return None, None
            return (f"{avg_col}{row + 1}",
                    f"=({avg_col}{row}-{prev_avg_col}{row})/{prev_avg_col}{row}%")

        plan = []
        for rid, row in RES_ROW.items():
            gcell, gf = growth_for(row)
            plan.append((row, int(round(by_res[rid])), f"={sale_col}{row}/{N}", gcell, gf))
        if total is not None:
            # Total row: static Sale value + its own Avg/day formula (rows 3,5..23).
            gcell, gf = growth_for(TOTAL_ROW)
            plan.append((TOTAL_ROW, int(round(total)), f"={sale_col}{TOTAL_ROW}/{N}", gcell, gf))
        plan.sort()

        for row, sale, avg, gcell, gf in plan:
            name = next((config.SHORT.get(r, r) for r, rw in RES_ROW.items() if rw == row),
                        "Nutriobox TOTAL")
            print(f"  row {row:>2} {str(name):<18} {sale_col}{row}={sale:>10}"
                  + (f"   {avg_col}{row}={avg}" if avg else "   (Total, no avg)")
                  + (f"   {gcell}={gf}" if gf else ""))

        if args.selftest or args.dry_run:
            print("\n(dry) nothing written." if args.dry_run else "\nselftest OK — column located, nothing written.")
            return 0

        # ---- write ----
        w.select_tab(TAB)
        for row, sale, avg, gcell, gf in plan:
            w.write_cell(f"{sale_col}{row}", sale)
            if avg:
                w.write_cell(f"{avg_col}{row}", avg)
            if gf:
                w.write_cell(gcell, gf)

        # ---- verify Sale values read back ----
        grid2 = w.read_tab(TAB)
        problems = []
        for rid, row in RES_ROW.items():
            want = int(round(by_res[rid]))
            got = (grid2[row - 1][j] if len(grid2) >= row and j < len(grid2[row - 1]) else "")
            try:
                ok = abs(float(str(got).replace(",", "")) - want) < 1
            except ValueError:
                ok = False
            if not ok:
                problems.append(f"{config.SHORT.get(rid, rid)}: wrote {want}, sheet {got!r}")
        if problems:
            print("\nVERIFY FAILED:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"\nwrote + verified Sale col {sale_col} (rows 3,5..23) + Avg/day {avg_col}. Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
