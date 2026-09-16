"""
Weekly Dining/Delivery % fill -> Playwright port of the Claude
"weekly-petpooja-dining-delivery-update" task (Mon 8 AM).

For each outlet (skip Sec 63) computes month-to-date (1st .. yesterday):
    Delivery sale %  = Delivery sale  / Total Sales      * 100
    Delivery orders% = Delivery orders / Successful orders * 100
and writes them into the current month's two columns of the Sales Data
"Dining/ Dlvry" tab. Row 3 (Nutriobox overall) gets ONLY the sale-% column, from
the All-Outlets "X% of sales generated from Online" figure.

    python dining_delivery.py --selftest / --dry-run / --headed / (live)
    python dining_delivery.py --dry-run --to 2026-09-06

VALIDATE BEFORE SCHEDULING (needs the live Petpooja session):
  * Per-outlet read: this switches to each outlet (page reloads), sets the per-outlet
    daterangepicker #synced_rangepicker, and reads the Total Sales / Delivery /
    Successful-orders cards. CONFIRM the card selectors/labels in read_outlet_cards()
    against the live dashboard (they moved in the Petpooja UI overhaul). The dashboard
    JSON does NOT expose per-outlet delivery split, so this is a DOM read.
  * All-Outlets overall: uses #statisticsdaterange + the Online% subtext for row 3.
  * Confirm the "Dining/ Dlvry" month block columns via the row-1 header.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

import config
from monthly_sales_fill import parse_month_header

IST = timezone(timedelta(hours=5, minutes=30))
SALES_SHEET_ID = config.SALES_DATA_SHEET_ID

# outlet -> (petpooja res_id, sheet row on the Dining/ Dlvry tab). Sec 63 excluded.
OUTLETS = [
    ("Prashant Vihar", 9960, 5),
    ("Janakpuri", 19652, 7),
    ("Karkardooma", 16011, 9),
    ("Dwarka", 62697, 11),
    ("Shivalik", 62695, 13),
    ("Noida", 80991, 15),          # Advant (exclude Sector 63)
    ("Rajinder Nagar", 159181, 17),
    ("DLF Phase 2", 349767, 19),
    ("Sector 15, Gurugram", 369621, 21),
]
NUTRIOBOX_ROW = 3   # overall: sale-% column ONLY


def _r2(x):
    try:
        return round(float(str(x).replace(",", "").replace("%", "")) + 0.0, 2)
    except (TypeError, ValueError):
        return None


def read_outlet_cards(page, res_id: int, from_iso: str, to_iso: str) -> dict:
    """
    Switch to `res_id`, set the per-outlet date range, read the four card numbers.
    Returns {total_sales, delivery_sale, delivery_orders, successful_orders}.
    VALIDATE: the card selectors below are the moving part — confirm live.
    """
    raise NotImplementedError(
        "read_outlet_cards: confirm the per-outlet Delivery / Total-Sales / Successful "
        "card selectors on the live dashboard, then implement (VALIDATE).")


def read_overall_online_pct(page, from_iso: str, to_iso: str) -> float:
    """All-Outlets: the 'X% of sales generated from Online' figure for row 3."""
    raise NotImplementedError(
        "read_overall_online_pct: confirm #statisticsdaterange + Online% subtext (VALIDATE).")


def pull(to_date: date, headless: bool) -> dict:
    from playwright.sync_api import sync_playwright
    from browser_export import PROFILE_DIR
    frm = to_date.replace(day=1).isoformat()
    to = to_date.isoformat()
    out = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=headless,
            args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(f"{config.PETPOOJA_BASE}/users/dashboard", wait_until="domcontentloaded")
            page.wait_for_timeout(6000)
            for name, rid, row in OUTLETS:
                c = read_outlet_cards(page, rid, frm, to)
                ts, ds, do, so = (c["total_sales"], c["delivery_sale"],
                                  c["delivery_orders"], c["successful_orders"])
                out[name] = dict(
                    row=row,
                    sale_pct=_r2(ds / ts * 100) if ts else None,
                    orders_pct=_r2(do / so * 100) if so else None,
                )
            out["_overall_sale_pct"] = _r2(read_overall_online_pct(page, frm, to))
        finally:
            ctx.close()
    # fail-closed: every outlet must have both numbers
    bad = [n for n, v in out.items() if n != "_overall_sale_pct"
           and (v["sale_pct"] is None or v["orders_pct"] is None)]
    if bad:
        raise RuntimeError(f"dining/delivery: incomplete reads for {bad} — refusing to write")
    return out


def _find_month_block(row1, year, month):
    for j, cell in enumerate(row1):
        if parse_month_header(cell) == (year, month):
            return j
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", help="month-to-date end YYYY-MM-DD (default: yesterday)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    headless = not args.headed

    to_date = (datetime.strptime(args.to, "%Y-%m-%d").date() if args.to
               else datetime.now(IST).date() - timedelta(days=1))
    print(f"period      : {to_date.replace(day=1)} .. {to_date}")

    data = pull(to_date, headless)
    for name, rid, row in OUTLETS:
        v = data[name]
        print(f"  row {row:>2} {name:<20} sale%={v['sale_pct']}  orders%={v['orders_pct']}")
    print(f"  row  3 Nutriobox overall    sale%={data['_overall_sale_pct']}")

    if args.selftest or args.dry_run:
        print("\n(dry) nothing written.")
        return 0

    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(SALES_SHEET_ID)
        grid = w.read_tab("Dining/ Dlvry")
        j = _find_month_block(grid[0] if grid else [], to_date.year, to_date.month)
        if j is None:
            print(f"STOP: no {to_date:%b %Y} block on the Dining/ Dlvry tab.")
            return 1
        sale_col = _col(j + 1)          # left column of the month block
        orders_col = _col(j + 2)        # right column
        w.select_tab("Dining/ Dlvry")
        for name, rid, row in OUTLETS:
            v = data[name]
            w.write_cell(f"{sale_col}{row}", f"{v['sale_pct']}%")
            w.write_cell(f"{orders_col}{row}", f"{v['orders_pct']}%")
        w.write_cell(f"{sale_col}{NUTRIOBOX_ROW}", f"{data['_overall_sale_pct']}%")
    print("\nOK — wrote Dining/ Dlvry for the month block.")
    return 0


def _col(idx1: int) -> str:
    s = ""
    while idx1 > 0:
        idx1, r = divmod(idx1 - 1, 26)
        s = chr(65 + r) + s
    return s


if __name__ == "__main__":
    sys.exit(main())
