"""
Incentive — MONTHLY metrics (1st of month) -> Playwright port of the Claude
"incentive--monthly-metrics-1st-of-month" task.

Scores the calendar month that just ended and fills rows 3, 15, 18 (H..Q) of the
scored-month tab in the Incentive Structure sheet:
    row 3   Metric 1  Avg sale/day vs previous month  (Sales Data "Monthly" tab)
    row 15  Metric 5  % sale from delivery            (Sales Data "Dining/ Dlvry" tab)
    row 18  Metric 6  AOV                             (Sales Data "AOV" tab / Petpooja)

    python incentive_monthly.py --selftest / --dry-run / --headed / (live)
    python incentive_monthly.py --month 2026-08     # score a specific month

VALIDATE BEFORE SCHEDULING:
  * M6 (AOV): needs the AOV tab filled from Petpooja monthly Orders+Sales first, then
    scored against the tab's row-17 bands. That Petpooja pull is not wired here — see
    read_aov(). Only <480->0 and >570->4 are stated in the SKILL; confirm the middle
    bands from row 17 and pass them to score_m6_aov.
  * M1/M5 read the Sales Data sheet — confirm the "Monthly" and "Dining/ Dlvry" tab
    layouts still match (this is the same sheet monthly_sales_fill.py writes).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone, timedelta

import config
import incentive_common as inc
from monthly_sales_fill import parse_month_header, col_a1

IST = timezone(timedelta(hours=5, minutes=30))
SALES_SHEET_ID = config.SALES_DATA_SHEET_ID   # 1r9u4DMs...

# incentive short -> row in the "Monthly" tab (same outlet rows monthly_sales_fill uses)
MONTHLY_ROW = {"Rohini": 5, "JP": 7, "KKD": 9, "Dwarka": 11, "Shivalik": 13,
               "Sec142": 15, "RN": 17, "DLF": 19, "Sec15": 21, "Sec63": 23}
# "Dining/ Dlvry" tab uses the same outlet row layout.
DINING_ROW = dict(MONTHLY_ROW)


def _find_month_col(row1, year, month):
    """0-based index of a month block whose header == (year, month), else None."""
    for j, cell in enumerate(row1):
        if parse_month_header(cell) == (year, month):
            return j
    return None


def _num(s):
    try:
        return float(str(s).replace("%", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def read_avg_perday_pct(scored: date, headless: bool) -> dict:
    """Metric 1: (this_avg - prev_avg)/prev_avg*100 per outlet, from the Monthly tab.
    The Avg/day cells are FORMULAS, so we read the COMPUTED values via gviz (which,
    unlike the Dining/ Dlvry tab, lines up 1:1 with sheet rows here — same read
    monthly_sales_fill uses)."""
    prev = (scored.replace(day=1) - timedelta(days=1)).replace(day=1)
    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(SALES_SHEET_ID)
        grid = w.read_tab("Monthly")
    row1 = grid[0] if grid else []
    j_this = _find_month_col(row1, scored.year, scored.month)
    j_prev = _find_month_col(row1, prev.year, prev.month)
    if j_this is None or j_prev is None:
        raise RuntimeError(f"Monthly tab missing a month block "
                           f"(this={scored:%b %Y} col={j_this}, prev={prev:%b %Y} col={j_prev})")
    avg_this_col = j_this + 1      # Avg/day column index (0-based) = header col + 1
    avg_prev_col = j_prev + 1
    out = {}
    for short, r in MONTHLY_ROW.items():
        row = grid[r - 1] if len(grid) >= r else []
        a_this = _num(row[avg_this_col]) if len(row) > avg_this_col else None
        a_prev = _num(row[avg_prev_col]) if len(row) > avg_prev_col else None
        if a_this is None or a_prev is None:
            raise RuntimeError(f"M1: unreadable Avg/day for {short} (row {r})")
        out[short] = ((a_this - a_prev) / a_prev * 100.0) if a_prev else 0.0
    return out


def read_delivery_pct(scored: date, headless: bool) -> dict:
    """Metric 5: delivery-sale % per outlet for the scored month, from Dining/ Dlvry.
    Column located from the row-1 header; per-outlet values read via the Name Box."""
    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(SALES_SHEET_ID)
        row1 = (w.read_tab("Dining/ Dlvry") or [[]])[0]
        j = _find_month_col(row1, scored.year, scored.month)
        if j is None:
            raise RuntimeError(f"Dining/ Dlvry tab has no block for {scored:%b %Y}")
        sale_col = col_a1(j + 1)          # delivery-sale % = LEFT column of the block
        w.select_tab("Dining/ Dlvry")
        out = {}
        for short, r in DINING_ROW.items():
            v = _num(w.read_selected_value(f"{sale_col}{r}"))
            out[short] = v if v is not None else 0.0
    out.setdefault("Sec63", 0.0)   # cloud kitchen -> 0 if blank
    return out


# Petpooja res_id -> incentive short (for the AOV pull).
AOV_RES_TO_SHORT = {
    9960: "Rohini", 19652: "JP", 16011: "KKD", 62697: "Dwarka", 62695: "Shivalik",
    80991: "Sec142", 159181: "RN", 349767: "DLF", 369621: "Sec15", 136183: "Sec63",
}


def read_aov(scored: date, headless: bool) -> dict:
    """Metric 6: per-outlet AOV (= total_sales / total_orders) for the scored month,
    from the Petpooja dashboard JSON (/users/load_restaurants_wise_data/, All-Outlets).
    Validated live 2026-09-08 for Aug (DLF 498, Dwarka 559, Sec63 437, ...).
    NOTE: the SKILL also fills the Sales Data 'AOV' tab (B/C/D); this scores directly
    from Petpooja, which is equivalent for the metric. VALIDATE only the middle band
    cut-points against the tab's row-17 legend (endpoints <480->0 and >570->4 are
    fixed; score_m6_aov defaults to 480/510/540/570)."""
    import json as _json
    from playwright.sync_api import sync_playwright
    from browser_export import PROFILE_DIR, _is_logged_out
    from petpooja import SessionExpired
    first = scored.replace(day=1)
    last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(f"{config.PETPOOJA_BASE}/users/dashboard", wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(2500)
            if _is_logged_out(page):
                raise SessionExpired("Petpooja logged out — run refresh_tokens.py --login")
            raw = page.evaluate(
                "async ({f, t}) => { const r = await fetch('/users/load_restaurants_wise_data/', "
                "{method:'POST', credentials:'include', headers:{'Content-Type':"
                "'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest'}, "
                "body:'from_date=' + f + '&to_date=' + t}); return await r.text(); }",
                {"f": first.isoformat(), "t": last.isoformat()})
            data = _json.loads(raw)
        finally:
            ctx.close()
    out = {}
    for e in data.get("all_restaurant_statistics", []):
        short = AOV_RES_TO_SHORT.get(e.get("res_id"))
        if not short:
            continue
        try:
            o = float(e.get("total_orders") or 0)
            s = float(e.get("total_sales") or 0)
        except (TypeError, ValueError):
            continue
        out[short] = round(s / o) if o else 0
    missing = [x for x in inc.OUTLET_ORDER if x not in out]
    if missing:
        raise RuntimeError(f"AOV: missing outlets {missing} — refusing to score partial")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="scored month YYYY-MM (default: previous calendar month)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    headless = not args.headed

    if args.month:
        y, m = map(int, args.month.split("-"))
        scored = date(y, m, 1)
    else:
        scored = (datetime.now(IST).date().replace(day=1) - timedelta(days=1)).replace(day=1)
    tab = inc.month_tab_label(scored)
    print(f"scored month: {scored:%B %Y}\nmonth tab   : {tab!r}")

    pct = read_avg_perday_pct(scored, headless)      # M1
    dlv = read_delivery_pct(scored, headless)        # M5
    aov = read_aov(scored, headless)                 # M6 (raises until wired)

    m1 = {o: inc.score_m1_saleperday_pct(pct[o]) for o in inc.OUTLET_ORDER}
    m5 = {o: inc.score_m5_delivery_pct(dlv[o]) for o in inc.OUTLET_ORDER}
    m6 = {o: inc.score_m6_aov(aov[o]) for o in inc.OUTLET_ORDER}

    rows = {inc.ROW[1]: m1, inc.ROW[5]: m5, inc.ROW[6]: m6}
    for o in inc.OUTLET_ORDER:
        print(f"  {o:<8} M1={m1[o]}(pct {pct[o]:.1f}) M5={m5[o]}({dlv[o]}) M6={m6[o]}")

    if args.selftest or args.dry_run:
        print("\n(dry) nothing written.")
        return 0

    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(inc.INCENTIVE_SHEET_ID)
        # Monthly run OWNS tab creation: if the tab is missing, duplicate the template.
        if tab not in w.tab_titles():
            w.duplicate_tab("Sheet1", tab)
        problems = inc.write_metric_rows(w, tab, rows, require_tab=False)
    if problems:
        print("\nVERIFY FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"\nOK — wrote rows 3/15/18 (H..Q) on {tab!r}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
