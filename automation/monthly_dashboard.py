"""
Monthly Item-Wise Dashboard rebuild -> Playwright port of the Claude
"nutriobox-monthly-dashboard" task. Runs on the 1st (2nd if the 1st is a Sunday).

Appends the PREVIOUS calendar month to the rolling item-wise Power-BI HTML in
Downloads/NutrioBox_Reports/NutrioBox_Dashboard_Sep2025_<MMMYYYY>.html:
  - main records: Petpooja Order Summary Item CSV -> dedupe to invoice (SUCCESS ONLY)
    -> aggregate by (restaurant, category, item)  [Cancelled excluded entirely]
  - addon records: Addon report (view_report/31) per outlet, isAddon:1
  -> merge into const DATA=[...], extend MONTH_ORDER, save new dated file.

    python monthly_dashboard.py --selftest / --dry-run / --headed / (live)
    python monthly_dashboard.py --month 2026-08

The DETERMINISTIC core (dedupe/aggregate/merge/validate) is fully implemented here
straight from the task SKILL. The two PORTAL reads are the VALIDATE pieces:

VALIDATE BEFORE SCHEDULING:
  * export_month_csv(): the month Order-Summary-Item export + S3 download. The daily
    port's browser_export.export_order_csv is single-date; this needs the from..to
    month range. Confirm the export POST + the S3 path pattern
    (reportsfile-live.s3.../ordersummaryitem/<acct>/<restId>/...<from>_<to>.csv) and
    that a 403 just means "not ready yet" (poll). This is the export that has been
    403-ing when the Petpooja session is stale -> refresh_tokens.py --login first.
  * scrape_month_addons(): view_report/31 per outlet for the month (see SKILL Step 4
    driving notes: #re_filter_filed_1_23_0_from/_to, jQuery('.re_final_search').
    trigger('click'), ~15s post-nav + ~90s query waits, change_restaurant+navigate).
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

import config

csv.field_size_limit(100_000_000)

# id -> Petpooja restaurant_name (for the addon scrape / outlet checks)
OUTLET_ID_NAME = {
    349767: "NutrioBox ( DLF Phase 2)", 159181: "NutrioBox ( Rajinder Nagar)",
    136183: "NutrioBox ( Sector 63 Noida )", 62697: "NutrioBox (Dwarka)",
    19652: "NutrioBox (Janakpuri)", 16011: "NutrioBox (Karkardooma)",
    80991: "NutrioBox (Noida)", 9960: "NutrioBox (Prashant Vihar)",
    369621: "NutrioBox (Sector 15, Gurugram)", 62695: "NutrioBox (Shivalik)",
}
EXPECTED_OUTLETS = 10


def should_run(today: date) -> bool:
    """1st of month, or the 2nd when the 1st was a Sunday."""
    if today.day == 1 and today.weekday() != 6:
        return True
    if today.day == 2 and today.replace(day=1).weekday() == 6:
        return True
    return False


def prev_month_range(today: date):
    last = today.replace(day=1) - timedelta(days=1)
    first = last.replace(day=1)
    return first, last


# ---- PORTAL reads (VALIDATE) ---------------------------------------------------
def export_month_csv(from_iso: str, to_iso: str, out_dir, headless: bool):
    raise NotImplementedError("export_month_csv: wire the month Order-Summary-Item export + S3 download (VALIDATE)")


def scrape_month_addons(from_iso: str, to_iso: str, headless: bool) -> list[dict]:
    raise NotImplementedError("scrape_month_addons: wire view_report/31 per outlet for the month (VALIDATE)")


# ---- DETERMINISTIC processing (verbatim from the SKILL) ------------------------
def process_main_csv(csv_path: str, month_full: str):
    """Dedupe to invoice (SUCCESS ONLY) then aggregate by (restaurant, category, item)."""
    seen = set()
    invoice_records = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            restaurant = (row.get("restaurant_name") or "").strip()
            if "Test" in restaurant:
                continue
            if (row.get("status") or "").strip() != "Success":
                continue
            invoice_no = str(row.get("invoice_no") or "").strip()
            if not invoice_no:
                continue
            key = (restaurant, invoice_no)
            if key in seen:
                continue
            seen.add(key)
            category = (row.get("category_name") or "").strip()
            item = (row.get("item_name") or "").strip()
            if not restaurant or not category or not item:
                continue
            try: qty = float(row.get("item_quantity") or 0)
            except ValueError: qty = 0.0
            try: tot = float(row.get("total") or 0)
            except ValueError: tot = 0.0
            invoice_records.append((restaurant, category, item, qty, tot))

    agg = defaultdict(lambda: {"qty": 0.0, "totalSales": 0.0})
    for rest, cat, item, qty, tot in invoice_records:
        a = agg[(rest, cat, item)]
        a["qty"] += qty
        a["totalSales"] += tot

    records = [{"restaurant": r, "category": c, "item": i, "qty": v["qty"],
                "month": month_full, "totalSales": round(v["totalSales"], 2),
                "status": "Success"} for (r, c, i), v in agg.items()]
    return records, len(invoice_records)


def validate_main(records: list[dict]) -> list[str]:
    stats = defaultdict(lambda: {"count": 0, "qty": 0.0, "sales": 0.0})
    for r in records:
        s = stats[r["restaurant"]]
        s["count"] += 1; s["qty"] += r["qty"]; s["sales"] += r["totalSales"]
    warn = []
    if len(stats) < EXPECTED_OUTLETS:
        warn.append(f"MISSING OUTLETS: only {len(stats)}/10 -> {list(stats)}")
    for o, d in stats.items():
        if d["sales"] == 0:
            warn.append(f"ZERO SALES: {o}")
    if sum(r["qty"] for r in records) < 10000:
        warn.append("LOW TOTAL QTY (<10k)")
    if sum(r["totalSales"] for r in records) < 10_000_000:
        warn.append("LOW TOTAL SALES (<1Cr)")
    return warn


def merge_into_dashboard(new_records: list[dict], addon_records: list[dict],
                         month_full: str, month_short_year: str, first_day: date) -> str:
    dash_dir = glob.glob("/sessions/*/mnt/NutrioBox_Reports")
    dash_dir = dash_dir[0] if dash_dir else os.path.expanduser(r"~/Downloads/NutrioBox_Reports")
    cands = sorted(glob.glob(os.path.join(dash_dir, "NutrioBox_Dashboard_Sep2025_*.html")),
                   key=os.path.getmtime)
    if not cands:
        raise RuntimeError(f"no rolling dashboard found in {dash_dir}")
    with open(cands[-1], "r", encoding="utf-8") as f:
        content = f.read()

    m = re.search(r"const DATA=", content)
    start = m.end()
    end = content.find("];", start) + 1
    existing = json.loads(content[start:end])
    existing = [r for r in existing if r.get("month") != month_full]        # idempotent
    existing = [r for r in existing if r.get("status") != "Cancelled"]      # safety
    merged = existing + new_records + addon_records

    def fmt_num(n):
        if isinstance(n, float):
            return f"{n:.1f}" if n == int(n) else ("%.10f" % n).rstrip("0").rstrip(".")
        return str(n)

    def fmt_record(r):
        p = ('{"restaurant": ' + json.dumps(r["restaurant"]) +
             ', "category": ' + json.dumps(r["category"]) +
             ', "item": ' + json.dumps(r["item"]) +
             ', "qty": ' + fmt_num(r["qty"]) +
             ', "month": ' + json.dumps(r["month"]) +
             ', "totalSales": ' + fmt_num(r["totalSales"]))
        if r.get("status"):
            p += ', "status": ' + json.dumps(r["status"])
        if r.get("isAddon") == 1:
            p += ', "isAddon": 1'
        return p + "}"

    content = content[:start] + "[" + ", ".join(fmt_record(r) for r in merged) + "]" + content[end:]

    mo_re = re.compile(r"const MONTH_ORDER=\[([^\]]+)\];")
    mm = mo_re.search(content)
    months = [s.strip().strip("'") for s in mm.group(1).split(",")]
    if month_full not in months:
        months.append(month_full)
    content = mo_re.sub("const MONTH_ORDER=[" + ",".join(f"'{x}'" for x in months) + "];", content)

    title_re = re.compile(r"NutrioBox - Outlet Item Wise Report \(Sep 2025 [–-] [A-Za-z]{3} \d{4}\)")
    content = title_re.sub(f"NutrioBox - Outlet Item Wise Report (Sep 2025 – {month_short_year})", content)

    out_name = f"NutrioBox_Dashboard_Sep2025_{first_day.strftime('%b%Y')}.html"
    out_path = os.path.join(dash_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="scored month YYYY-MM (default: previous month)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--force", action="store_true", help="ignore the 1st/2nd run-day guard")
    args = ap.parse_args()
    headless = not args.headed

    today = date.today()
    if not args.month and not args.force and not should_run(today):
        print("SKIP: not the 1st (or the 2nd-after-Sunday). Use --force or --month to override.")
        return 0

    if args.month:
        y, mo = map(int, args.month.split("-"))
        first = date(y, mo, 1)
        last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    else:
        first, last = prev_month_range(today)
    from_iso, to_iso = first.isoformat(), last.isoformat()
    month_full = first.strftime("%B")
    month_short_year = first.strftime("%b %Y")
    print(f"month       : {month_full} {first.year}  ({from_iso} .. {to_iso})")

    out_dir = glob.glob("/sessions/*/mnt/outputs")
    out_dir = out_dir[0] if out_dir else "."
    csv_path = export_month_csv(from_iso, to_iso, out_dir, headless)      # VALIDATE
    main_records, invoices = process_main_csv(csv_path, month_full)
    print(f"invoices(Success)={invoices}  aggregated={len(main_records)}")
    warn = validate_main(main_records)
    outlets = len({r['restaurant'] for r in main_records})
    if outlets < 5 or len(main_records) < 50:
        print(f"ABORT: only {outlets} outlets / {len(main_records)} records — export failure.")
        return 1
    for w in warn:
        print("  WARN:", w)

    addon_records = scrape_month_addons(from_iso, to_iso, headless)       # VALIDATE

    if args.selftest or args.dry_run:
        print(f"(dry) main={len(main_records)} addon={len(addon_records)} — nothing written.")
        return 0

    out_path = merge_into_dashboard(main_records, addon_records, month_full, month_short_year, first)
    print(f"OK — wrote {out_path} ({os.path.getsize(out_path):,} bytes)")
    print("Next: deploy the item-wise HTML per the monthly-reminder flow.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
