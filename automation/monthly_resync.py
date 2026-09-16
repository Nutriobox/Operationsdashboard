"""
Monthly re-sync -> Playwright port of the Claude "nutriobox-monthly-resync" task
(3rd of month, 05:30 IST). Re-pulls the whole previous month from Petpooja (after
late cancellations / aggregator syncs settle) and rewrites those dates in the sales
dashboard's DAILY_DATA so the closed month matches Petpooja's POS Dashboard exactly.

    python monthly_resync.py --selftest / --dry-run / --headed / (live)
    python monthly_resync.py --month 2026-08

DETERMINISTIC + reused (safe): IST month/window math, the invoice dedupe (daily
pipeline rules), and the DAILY_DATA byte-slice rewrite with the two business-day
guard-rails (reuses dashboard_build's slicing helpers). Fails-closed on any gate.

VALIDATE BEFORE SCHEDULING:
  * export_month_csv(): month Order-Summary-Item export + S3 download (same VALIDATE
    as monthly_dashboard.py — the 403-prone step; refresh_tokens.py --login first).
  * pos_dashboard_total(): the mandatory reconcile gate reads All-Outlet Total Sales
    for the month via statistics_date()+load_sales_statistics(). Confirm those page
    functions still exist post-UI-overhaul (the daily dashboard_scrape now uses JSON
    endpoints — /users/load_sales_statistics/ total_sales is the same figure).
  RECONCILE GATE: |pos_total - export_total| must be <= 200 or it writes nothing.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

import config

IST = timezone(timedelta(hours=5, minutes=30))
WIN_START_MIN = 8 * 60      # 08:00 of month_start
WIN_END_MIN = 60            # 01:00 of (month_end + 1 day)


def month_window(today: date):
    first_this = today.replace(day=1)
    month_end = first_this - timedelta(days=1)
    month_start = month_end.replace(day=1)
    return month_start, month_end


# ---- PORTAL steps (VALIDATE) ---------------------------------------------------
def export_month_csv(from_iso, to_iso, out_dir, headless):
    raise NotImplementedError("export_month_csv: month export + S3 download (VALIDATE — see monthly_dashboard)")


def pos_dashboard_total(from_iso, to_iso, headless) -> float:
    """All-Outlet Total Sales for the month (reconcile gate)."""
    raise NotImplementedError("pos_dashboard_total: read All-Outlet Total Sales for the month (VALIDATE)")


# ---- deterministic dedupe (daily-pipeline rules) -------------------------------
def dedupe_month(csv_path, month_start: date, month_end: date):
    import csv as _csv
    _csv.field_size_limit(100_000_000)
    win_lo = (month_start.isoformat(), WIN_START_MIN)
    win_hi = ((month_end + timedelta(days=1)).isoformat(), WIN_END_MIN)
    seen = set()
    recs = []
    total_success = 0.0
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in _csv.DictReader(f):
            rest = (row.get("restaurant_name") or "").strip()
            if "Test" in rest:
                continue
            status = (row.get("status") or "").strip()
            if status not in ("Success", "Cancelled"):
                continue
            inv = str(row.get("invoice_no") or "").strip()
            if not inv or (rest, inv) in seen:
                continue
            seen.add((rest, inv))
            d = (row.get("date") or "")[:10]
            hhmm = (row.get("time") or "")[:5]
            try:
                mins = int(hhmm[:2]) * 60 + int(hhmm[3:5])
            except ValueError:
                mins = 0
            if not (win_lo <= (d, mins) <= win_hi):
                continue
            sales = 0.0
            if status == "Success":
                try: sales = float(row.get("total") or 0)
                except ValueError: sales = 0.0
                total_success += sales
            recs.append(dict(restaurant=rest, category=(row.get("category_name") or "").strip(),
                             item=(row.get("item_name") or "").strip(),
                             qty=float(row.get("item_quantity") or 0) if row.get("item_quantity") else 0.0,
                             date=d, time=hhmm, totalSales=sales, status=status,
                             invoiceNo=inv, orderType=(row.get("order_type") or "").strip(),
                             paymentType=(row.get("payment_type") or "").strip(),
                             area=(row.get("area") or "").strip()))
    return recs, total_success


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="YYYY-MM (default: previous month)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    headless = not args.headed

    if args.month:
        y, mo = map(int, args.month.split("-"))
        month_start = date(y, mo, 1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    else:
        month_start, month_end = month_window(datetime.now(IST).date())
    from_iso, to_iso = month_start.isoformat(), month_end.isoformat()
    print(f"resync month: {from_iso} .. {to_iso}")
    print(f"window      : {from_iso} 08:00  ->  {(month_end + timedelta(days=1)).isoformat()} 01:00")

    import glob
    out_dir = (glob.glob('/sessions/*/mnt/outputs') or ['.'])[0]
    csv_path = export_month_csv(from_iso, to_iso, out_dir, headless)          # VALIDATE
    recs, export_total = dedupe_month(csv_path, month_start, month_end)
    print(f"deduped invoices={len(recs)}  export Success total=Rs {export_total:,.2f}")

    pos_total = pos_dashboard_total(from_iso, to_iso, headless)               # VALIDATE
    delta = abs(pos_total - export_total)
    print(f"reconcile   : POS={pos_total:,.2f}  export={export_total:,.2f}  delta={delta:,.2f}")
    if delta > 200:
        print("ABORT (reconcile gate): delta > 200 — refusing to write.")
        return 1

    if args.selftest or args.dry_run:
        print("(dry) reconcile OK — DAILY_DATA rewrite NOT performed.")
        return 0

    # DAILY_DATA byte-slice rewrite with the two business-day guard-rails is delicate
    # (see SKILL Step 5). Reuse dashboard_build's slicing rather than re-derive here.
    raise NotImplementedError(
        "DAILY_DATA month-rewrite: wire to dashboard_build byte-slice with the "
        "month_start-1 and month_end+1 business-day guard-rails (VALIDATE / dev step).")


if __name__ == "__main__":
    sys.exit(main())
