"""
Discount Analytics weekly refresh  (native Playwright port).

Rebuilds  public/nutriobox-discount-dashboard.html  from the most recent
COMPLETED Mon-Sun week of Petpooja "Order Summary (item)" data, plus the
Data-tab workbook it serves.  No Claude tokens.

A "defined discount tier" order = discount % (= round(discount/my_amount*100,1))
exactly equal to 10, 20, 50 or 100  (the round staff / loyalty discounts;
aggregator promos such as 42.6% are excluded).

    python discount_weekly.py --selftest            # fetch + compute, write nothing
    python discount_weekly.py --dry-run             # + preview, write nothing
    python discount_weekly.py --dry-run --monday 2026-08-24
    python discount_weekly.py --csv a.csv b.csv     # use given CSVs (offline test)
    python discount_weekly.py --headed              # live, visible browser
    python discount_weekly.py                       # live (scheduled mode)
    python discount_weekly.py --publish             # live + git commit + PUSH-discount.bat

The Petpooja pull is browser_export.export_order_csv — the SAME Playwright export
the sales and momos jobs already use, so this adds no new browser surface.
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

# config is only needed for the live Petpooja pull; keep the build path importable
# anywhere (offline --csv testing) even when config/playwright are absent.
try:
    import config  # noqa
    REPO = config.ROOT.parent
except Exception:
    REPO = Path(__file__).resolve().parent.parent

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "discount_template.html"
PUBLIC_HTML = REPO / "public" / "nutriobox-discount-dashboard.html"
PUSH_BAT = REPO / "PUSH-discount.bat"

TIERS = (10, 20, 50, 100)
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Workbook column layouts (mirror the manual "regular_discount" report).
MASTER_COLS = ["restaurant_name", "invoice_no", "date", "payment_type", "order_type",
               "status", "area", "virtual_brand_name", "brand_grouping",
               "customer_phone", "customer_name", "Discount %", "my_amount",
               "total_tax", "discount", "total", "item_name", "category_name",
               "item_price", "item_quantity", "item_total"]
TIER_COLS = ["restaurant_name", "invoice_no", "date", "order_type", "status",
             "customer_phone", "customer_name", "my_amount (₹)", "discount (₹)",
             "Discount %", "total (₹)", "item_name", "category_name"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def resolve_week(monday_arg: str | None) -> tuple[date, date]:
    """Most recently COMPLETED Mon-Sun week (Sunday strictly before today)."""
    if monday_arg:
        mon = datetime.strptime(monday_arg, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            raise SystemExit(f"--monday {monday_arg} is a {mon.strftime('%A')}, not Monday")
        return mon, mon + timedelta(days=6)
    today = date.today()
    last_sunday = today - timedelta(days=today.weekday() + 1)
    return last_sunday - timedelta(days=6), last_sunday


def span_label(mon: date, sun: date) -> str:
    if mon.month == sun.month:
        return f"{mon.day}-{sun.day} {MONTH_ABBR[sun.month-1]} {sun.year}"
    return f"{mon.day} {MONTH_ABBR[mon.month-1]} - {sun.day} {MONTH_ABBR[sun.month-1]} {sun.year}"


def fnum(x):
    try:
        return float(str(x).strip())
    except Exception:
        return None


def parse_dt(s: str) -> datetime | None:
    s = (s or "").strip()
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%m/%d/%y %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def outlet_short(restaurant_name: str) -> str:
    m = re.search(r"\((.*)\)", restaurant_name or "")
    return (m.group(1).strip() if m else (restaurant_name or "").strip())


# ---------------------------------------------------------------------------
# clean + classify
# ---------------------------------------------------------------------------
def clean_rows(rows: list[dict]) -> list[dict]:
    """Dedupe invoice_no, keep Success only, add Discount % = round(disc/my*100,1)."""
    seen, out = set(), []
    for r in rows:
        if (r.get("status") or "").strip() != "Success":
            continue
        iv = r.get("invoice_no")
        if iv in seen:
            continue
        seen.add(iv)
        my, d = fnum(r.get("my_amount")), fnum(r.get("discount"))
        r = dict(r)
        r["Discount %"] = round(d / my * 100, 1) if (my and d is not None) else 0.0
        out.append(r)
    return out


def tier_of(r: dict) -> int | None:
    p = r.get("Discount %")
    ip = int(p) if p is not None else None
    return ip if (ip in TIERS and float(ip) == p) else None


# ---------------------------------------------------------------------------
# build the embedded ORDERS model
# ---------------------------------------------------------------------------
def build_orders(clean: list[dict], mon: date, sun: date) -> tuple[list[dict], dict]:
    O = []
    for r in clean:
        lv = tier_of(r)
        if not lv:
            continue
        dt = parse_dt(r.get("date"))
        if not dt or not (mon <= dt.date() <= sun):
            continue
        my = fnum(r.get("my_amount")) or 0
        ip = fnum(r.get("item_total")) or 0
        O.append({
            "o": outlet_short(r.get("restaurant_name")),
            "d": dt.strftime("%Y-%m-%d"),
            "tm": dt.strftime("%H:%M"),
            "l": lv,
            "ds": round(fnum(r.get("discount")) or 0, 1),
            "b": round(my),
            "it": (r.get("item_name") or "").strip(),
            "ip": round(ip),
            "cat": (r.get("category_name") or "").strip(),
            "mi": 1 if (my - ip) > 1 else 0,
            "c": (r.get("customer_name") or "").strip(),
            "p": (r.get("customer_phone") or "").strip(),
            "ch": (r.get("area") or "").strip(),
        })
    O.sort(key=lambda x: (x["d"], x["tm"]))
    outlets = sorted({x["o"] for x in O})
    meta = {"from": mon.isoformat(), "to": sun.isoformat(), "outlets": outlets}
    return O, meta


# ---------------------------------------------------------------------------
# build the Data-tab workbook (6 sheets, mirrors the manual report)
# ---------------------------------------------------------------------------
def build_workbook(clean: list[dict]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    numeric = {"Discount %", "my_amount", "total_tax", "discount", "total",
               "item_price", "item_quantity", "item_total",
               "my_amount (₹)", "discount (₹)", "total (₹)"}
    src_for = {"my_amount (₹)": "my_amount", "discount (₹)": "discount",
               "total (₹)": "total"}

    def cell(r, col):
        key = src_for.get(col, col)
        v = r.get(key, "")
        if col in numeric:
            fv = fnum(v)
            return fv if fv is not None else (v if v not in (None,) else "")
        return v

    wb = Workbook()
    # master
    ws = wb.active
    ws.title = "Order_Summary_Item_Report"
    ws.append(MASTER_COLS)
    for r in clean:
        ws.append([cell(r, c) for c in MASTER_COLS])

    # per-tier
    for lv in TIERS:
        wsx = wb.create_sheet(f"{lv}%")
        wsx.append(TIER_COLS)
        for r in clean:
            if tier_of(r) == lv:
                wsx.append([cell(r, c) for c in TIER_COLS])

    # customer regularity
    reg: dict[str, dict] = {}
    for r in clean:
        lv = tier_of(r)
        if not lv:
            continue
        name = (r.get("customer_name") or "").strip() or (r.get("customer_phone") or "").strip() or "(blank)"
        key = (r.get("customer_phone") or "").strip() or name.lower()
        g = reg.setdefault(key, {"name": name, 10: 0, 20: 0, 50: 0, 100: 0, "disc": 0.0})
        if r.get("customer_name"):
            g["name"] = r["customer_name"].strip()
        g[lv] += 1
        g["disc"] += fnum(r.get("discount")) or 0
    wsr = wb.create_sheet("Customer Regularity")
    wsr.append(["Customer", "Times 10%", "Times 20%", "Times 50%",
                "Times 100%", "Total times", "Total discount (₹)"])
    for g in sorted(reg.values(), key=lambda x: -(x[10]+x[20]+x[50]+x[100])):
        tot = g[10] + g[20] + g[50] + g[100]
        wsr.append([g["name"], g[10], g[20], g[50], g[100], tot, round(g["disc"], 1)])

    for sh in wb.worksheets:
        for c in sh[1]:
            c.font = Font(bold=True)
        sh.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def render(orders: list[dict], meta: dict, workbook: bytes) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    odata = json.dumps({"O": orders, "META": meta}, separators=(",", ":"), ensure_ascii=False)
    b64 = base64.b64encode(workbook).decode()
    out = tpl.replace("/*__ODATA__*/", odata).replace('"/*__REPORTB64__*/"', '"' + b64 + '"')
    if "/*__ODATA__*/" in out or '"/*__REPORTB64__*/"' in out:
        raise SystemExit("template placeholders not filled — aborting")
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--monday", help="Monday of the week to build (YYYY-MM-DD)")
    ap.add_argument("--csv", nargs="+", help="use these CSV files instead of pulling Petpooja")
    ap.add_argument("--headed", action="store_true", help="visible browser for the pull")
    ap.add_argument("--selftest", action="store_true", help="fetch + compute, write nothing")
    ap.add_argument("--dry-run", action="store_true", help="+ preview, write nothing")
    ap.add_argument("--publish", action="store_true", help="after write: git commit + PUSH-discount.bat")
    ap.add_argument("--out", help="write the HTML here instead of public/ (testing)")
    args = ap.parse_args()

    mon, sun = resolve_week(args.monday)
    span = span_label(mon, sun)
    print(f"week        : {span}  ({mon} .. {sun})")

    # ---- pull -------------------------------------------------------------
    if args.csv:
        paths = [Path(c) for c in args.csv]
    else:
        from browser_export import export_order_csv
        tmp = Path(tempfile.mkdtemp(prefix="discount_"))
        paths, cur = [], mon
        while cur <= sun:
            paths.append(export_order_csv(cur.isoformat(), tmp, tag="1",
                                          headless=not args.headed))
            cur += timedelta(days=1)
    rows: list[dict] = []
    for p in paths:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            rows.extend(csv.DictReader(fh))
    print(f"csv files   : {len(paths)}   rows: {len(rows):,}")

    clean = clean_rows(rows)
    week = [r for r in clean if (parse_dt(r.get('date')) and mon <= parse_dt(r['date']).date() <= sun)]
    orders, meta = build_orders(clean, mon, sun)
    disc_total = round(sum(o["ds"] for o in orders))
    per = {t: sum(1 for o in orders if o["l"] == t) for t in TIERS}
    print(f"success rows: {len(week):,}   tiered orders: {len(orders):,}   "
          f"discount ₹{disc_total:,}")
    print(f"tiers       : 10%={per[10]}  20%={per[20]}  50%={per[50]}  100%={per[100]}")

    # ---- sanity gates -----------------------------------------------------
    errs = []
    if len(week) == 0:
        errs.append("no Success orders pulled for the week — fetch likely failed")
    if len(orders) == 0:
        errs.append("no defined-tier (10/20/50/100%) orders found")
    if errs:
        print("\nSANITY FAILED — nothing written:")
        for e in errs:
            print(f"  - {e}")
        return 1
    if len(orders) < 80:
        print(f"note        : only {len(orders)} tiered orders — light week (proceeding)")
    print("sanity      : OK")

    if args.selftest:
        print("\nselftest only — nothing written.")
        return 0
    if args.dry_run:
        print("\ndry run — computed, nothing written.")
        return 0

    # ---- build + write ----------------------------------------------------
    workbook = build_workbook(clean)
    html = render(orders, meta, workbook)
    dest = Path(args.out) if args.out else PUBLIC_HTML
    dest.write_text(html, encoding="utf-8")
    print(f"written     : {dest}  ({len(html):,} bytes, workbook {len(workbook):,} b)")

    # verify what we wrote
    back = dest.read_text(encoding="utf-8")
    if ('"O":' not in back) or ("REPORT_B64" not in back) or ('class="brand"' in back):
        print("VERIFY FAILED — restore with: git checkout -- public/nutriobox-discount-dashboard.html")
        return 1
    print("verify      : OK")

    if args.publish and not args.out:
        subprocess.run(["git", "config", "user.email", "mayank@nutriobox.com"], cwd=REPO, check=True)
        subprocess.run(["git", "config", "user.name", "Mayank"], cwd=REPO, check=True)
        subprocess.run(["git", "add", str(PUBLIC_HTML)], cwd=REPO, check=True)
        msg = (f"Discount Analytics: week {span} — {len(orders)} tiered orders, "
               f"discount {disc_total}\n\n"
               f"Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>\n"
               f"Claude-Session: https://claude.ai/code/session_01UB5nTUHmgq6U1UERW2ashS")
        subprocess.run(["git", "commit", "-m", msg], cwd=REPO, check=True)
        subprocess.run([str(PUSH_BAT)], cwd=REPO, shell=True)
        print("published   : committed + PUSH-discount.bat launched")
    else:
        print("\nNOT pushed. Run PUSH-discount.bat (or re-run with --publish).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
