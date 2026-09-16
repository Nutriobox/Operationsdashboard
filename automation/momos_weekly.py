"""
Momos Weekly Performance → Playwright (port of the Cowork task
`nutriobox-momos-dashboard--weekly-update-higgsfield`).

Appends exactly one completed Mon–Sun week to the self-hosted dashboard
(public/nutriobox-momos-dashboard.html + the identical root copy). No Claude
tokens.

    python momos_weekly.py --selftest            # export + compute, write nothing
    python momos_weekly.py --dry-run             # + reconcile preview, write nothing
    python momos_weekly.py --dry-run --monday 2026-08-24
    python momos_weekly.py --headed              # live, visible browser
    python momos_weekly.py                       # live (scheduled mode)
    python momos_weekly.py --publish             # live + git commit + PUSH-momos.bat

The Petpooja pull is `browser_export.export_order_csv` — the SAME Playwright
export the sales job already uses, so this port adds no new browser surface.

IMPORTANT — schema note (2026-08-27): the `const D` object was rebuilt by commit
2a6cfab and no longer matches the old SKILL text. The real keys are flat arrays
(`oSales`, `vVegSales`, ...), NOT `outlets.*` / `tblVeg` / `variantSplit`.
This module targets the REAL schema, verified against the live file.

Every one of the 11 invariants that hold on the current file is re-checked after
the append; if any breaks, nothing is written.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import config

REPO = config.ROOT.parent
PUBLIC_HTML = REPO / "public" / "nutriobox-momos-dashboard.html"
ROOT_HTML = REPO / "nutriobox-momos-dashboard.html"
PUSH_BAT = REPO / "PUSH-momos.bat"

MOMO_MATCH = "whole wheat momos"
VARIANTS = ["Steamed", "Tandoori", "Chilli Sauce"]

# Dashboard outlet order (D["outletNames"]).
OUTLET_ORDER = ["Prashant Vihar", "Dwarka", "Karkardooma", "Janakpuri",
                "Rajinder Nagar", "DLF Phase 2", "Shivalik", "Noida",
                "Sector 63 Noida", "Sector 15, Gurugram"]

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------------------------------------------------------------------------
# Week resolution
# ---------------------------------------------------------------------------
def resolve_week(monday_arg: str | None) -> tuple[date, date]:
    """Most recently COMPLETED Mon–Sun week (Sunday strictly before today)."""
    if monday_arg:
        mon = datetime.strptime(monday_arg, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            raise SystemExit(f"--monday {monday_arg} is a {mon.strftime('%A')}, not Monday")
        return mon, mon + timedelta(days=6)
    today = date.today()
    last_sunday = today - timedelta(days=today.weekday() + 1)
    return last_sunday - timedelta(days=6), last_sunday


def span_label(mon: date, sun: date) -> str:
    """'Aug 10–16' or 'Jul 27–Aug 2' (en dash, matching the file)."""
    a = f"{MONTH_ABBR[mon.month - 1]} {mon.day}"
    b = f"{sun.day}" if mon.month == sun.month else f"{MONTH_ABBR[sun.month - 1]} {sun.day}"
    return f"{a}–{b}"


# ---------------------------------------------------------------------------
# CSV -> one week of momo numbers
# ---------------------------------------------------------------------------
def _norm_outlet(restaurant_name: str) -> str | None:
    """
    Map Petpooja's restaurant_name to a dashboard outlet.

    Matches on the text inside parentheses, normalising spaces/commas. 'Noida'
    and 'Sector 63 Noida' are deliberately kept distinct.
    """
    m = re.search(r"\(([^)]*)\)", restaurant_name or "")
    inner = (m.group(1) if m else restaurant_name or "").strip()
    key = re.sub(r"[\s,]+", " ", inner).strip().lower()
    for name in OUTLET_ORDER:
        if re.sub(r"[\s,]+", " ", name).strip().lower() == key:
            return name
    return None


def _variant(item_name: str) -> str | None:
    n = (item_name or "").lower()
    if "steamed" in n:
        return "Steamed"
    if "tandoori" in n:
        return "Tandoori"
    if "chilli" in n:
        return "Chilli Sauce"
    return None


def _num(v) -> float:
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(v)) or 0)
    except ValueError:
        return 0.0


def compute_week(csv_paths: list[Path]) -> dict:
    """
    Aggregate the week from one or more Order Summary Item CSVs.

    Recipe (unchanged from the SKILL): drop exact-duplicate rows, keep
    status == Success, momo items = item_name contains 'Whole Wheat Momos',
    veg/nonveg by 'Chicken' prefix, variant by Steamed/Tandoori/Chilli.
    """
    seen: set[tuple] = set()
    o_sales = {n: 0.0 for n in OUTLET_ORDER}
    o_units = {n: 0.0 for n in OUTLET_ORDER}
    o_veg_s = {n: 0.0 for n in OUTLET_ORDER}
    o_non_s = {n: 0.0 for n in OUTLET_ORDER}
    o_veg_u = {n: 0.0 for n in OUTLET_ORDER}
    o_non_u = {n: 0.0 for n in OUTLET_ORDER}
    v_veg_s = {v: 0.0 for v in VARIANTS}
    v_non_s = {v: 0.0 for v in VARIANTS}
    v_veg_u = {v: 0.0 for v in VARIANTS}
    v_non_u = {v: 0.0 for v in VARIANTS}
    invoices: set[str] = set()

    def col(row: dict, *names):
        for n in names:
            for k in row:
                if k and k.strip().lower() == n:
                    return row[k]
        return None

    for path in csv_paths:
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
            for row in csv.DictReader(fh):
                key = tuple((row.get(k) or "") for k in sorted(row))
                if key in seen:
                    continue
                seen.add(key)

                status = (col(row, "status", "order status") or "").strip().lower()
                if status != "success":
                    continue

                item = col(row, "item_name", "item name") or ""
                if MOMO_MATCH not in item.lower():
                    continue

                outlet = _norm_outlet(col(row, "restaurant_name", "restaurant name") or "")
                var = _variant(item)
                if not outlet or not var:
                    continue

                sales = _num(col(row, "item_total", "item total"))
                units = _num(col(row, "item_quantity", "item quantity", "quantity"))
                nonveg = item.strip().lower().startswith("chicken")

                o_sales[outlet] += sales
                o_units[outlet] += units
                if nonveg:
                    o_non_s[outlet] += sales
                    o_non_u[outlet] += units
                    v_non_s[var] += sales
                    v_non_u[var] += units
                else:
                    o_veg_s[outlet] += sales
                    o_veg_u[outlet] += units
                    v_veg_s[var] += sales
                    v_veg_u[var] += units

                inv = col(row, "invoice_no", "invoice no", "invoice")
                if inv:
                    invoices.add(str(inv).strip())

    r = lambda d: [int(round(d[n])) for n in OUTLET_ORDER]
    rv = lambda d: {v: int(round(d[v])) for v in VARIANTS}
    return {
        "oSales": r(o_sales), "oUnits": r(o_units),
        "oVegSales": r(o_veg_s), "oNonSales": r(o_non_s),
        "oVegUnits": r(o_veg_u), "oNonUnits": r(o_non_u),
        "vVegSales": rv(v_veg_s), "vNonSales": rv(v_non_s),
        "vVegUnits": rv(v_veg_u), "vNonUnits": rv(v_non_u),
        "orders": len(invoices),
    }


# ---------------------------------------------------------------------------
# HTML data object
# ---------------------------------------------------------------------------
def load_D(html: str) -> tuple[dict, int, int]:
    """
    Parse `const D = {...}`. Anchors past the header comment, which contains a
    decoy 'const D = { ... }' string (this is the trap the SKILL warns about).
    """
    m = re.search(r'const\s+D\s*=\s*\{', html)
    while m and "{ ... }" in html[m.start():m.start() + 40]:
        m = re.search(r'const\s+D\s*=\s*\{', html[m.end():])
        if not m:
            break
    m = None
    for cand in re.finditer(r'const\s+D\s*=\s*\{', html):
        if '"weekLabels"' in html[cand.end() - 1:cand.end() + 200]:
            m = cand
            break
    if not m:
        raise RuntimeError("could not locate the real `const D = {` object")
    start = m.end() - 1
    depth = 0
    for k in range(start, len(html)):
        if html[k] == "{":
            depth += 1
        elif html[k] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start:k + 1]), start, k + 1
    raise RuntimeError("unbalanced braces in the D object")


def reconcile(D: dict) -> list[str]:
    """The 11 invariants that hold on the published file."""
    K = D["kpi"]
    sv = lambda d: sum(sum(v) for v in d.values())
    checks = [
        ("sum(weekly.sales) == kpi.sales", sum(D["weekly"]["sales"]), K["sales"]),
        ("sum(oSales) == kpi.sales", sum(sum(w) for w in D["oSales"]), K["sales"]),
        ("sum(oVegSales) == kpi.vegSales", sum(sum(w) for w in D["oVegSales"]), K["vegSales"]),
        ("sum(vVegSales) == kpi.vegSales", sv(D["vVegSales"]), K["vegSales"]),
        ("sum(oNonSales) == kpi.nonvegSales", sum(sum(w) for w in D["oNonSales"]), K["nonvegSales"]),
        ("sum(vNonSales) == kpi.nonvegSales", sv(D["vNonSales"]), K["nonvegSales"]),
        ("sum(weekly.units) == kpi.units", sum(D["weekly"]["units"]), K["units"]),
        ("sum(oUnits) == kpi.units", sum(sum(w) for w in D["oUnits"]), K["units"]),
        ("vegUnits + nonvegUnits == units", K["vegUnits"] + K["nonvegUnits"], K["units"]),
        ("sum(weekly.orders) == kpi.orders", sum(D["weekly"]["orders"]), K["orders"]),
        ("round(sales/orders) == kpi.aov", round(K["sales"] / K["orders"]) if K["orders"] else 0, K["aov"]),
    ]
    return [f"{n}: {a:,} vs {b:,}" for n, a, b in checks if a != b]


def append_week(D: dict, wk: dict, span: str) -> dict:
    """Append exactly one week and roll the cumulative KPI block."""
    if span in D["weekSpans"]:
        raise RuntimeError(f"week {span!r} is already published (idempotency guard)")

    D["weekLabels"].append(f"Wk{len(D['weekLabels']) + 1}")
    D["weekSpans"].append(span)

    sales = sum(wk["oSales"])
    units = sum(wk["oUnits"])
    D["weekly"]["sales"].append(sales)
    D["weekly"]["units"].append(units)
    D["weekly"]["orders"].append(wk["orders"])

    for key in ("oSales", "oUnits", "oVegSales", "oNonSales", "oVegUnits", "oNonUnits"):
        D[key].append(wk[key])
    for key in ("vVegSales", "vNonSales", "vVegUnits", "vNonUnits"):
        for v in VARIANTS:
            D[key][v].append(wk[key][v])

    K = D["kpi"]
    K["sales"] += sales
    K["units"] += units
    K["orders"] += wk["orders"]
    K["vegSales"] += sum(wk["oVegSales"])
    K["nonvegSales"] += sum(wk["oNonSales"])
    K["vegUnits"] += sum(wk["oVegUnits"])
    K["nonvegUnits"] += sum(wk["oNonUnits"])
    K["aov"] = round(K["sales"] / K["orders"]) if K["orders"] else 0
    return D


def render(html: str, D: dict, start: int, end: int, sun: date) -> str:
    """Splice D back in and roll the PERIOD end date + <title>."""
    out = html[:start] + json.dumps(D, ensure_ascii=False) + html[end:]
    end_label = f"{sun.day} {MONTH_ABBR[sun.month - 1]}"
    out = re.sub(r'(const PERIOD\s*=\s*"1 Jun – )[^"]*(")',
                 rf'\g<1>{end_label} {sun.year}\g<2>', out)
    out = re.sub(r'(<title>NutrioBox Momos Dashboard — 1 Jun – )[^<]*(</title>)',
                 rf'\g<1>{end_label} {sun.year}\g<2>', out)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--monday", help="Monday of the target week (YYYY-MM-DD)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--publish", action="store_true",
                    help="after a successful write, git commit and run PUSH-momos.bat")
    ap.add_argument("--csv", nargs="*", help="use existing CSV(s) instead of exporting")
    args = ap.parse_args()

    mon, sun = resolve_week(args.monday)
    span = span_label(mon, sun)
    print(f"target week : {mon} .. {sun}  ({span})")

    html = PUBLIC_HTML.read_text(encoding="utf-8")
    D, start, end = load_D(html)
    print(f"published   : {len(D['weekLabels'])} weeks, last = {D['weekSpans'][-1]}")

    if span in D["weekSpans"]:
        print(f"\nalready published ({span}) — nothing to do.")
        return 0

    pre = reconcile(D)
    if pre:
        print("\nPUBLISHED FILE DOES NOT RECONCILE — refusing to touch it:")
        for p in pre:
            print(f"  - {p}")
        return 1
    print("baseline    : reconciles (11/11)")

    # ---- pull -------------------------------------------------------------
    if args.csv:
        paths = [Path(c) for c in args.csv]
    else:
        from browser_export import export_order_csv
        tmp = Path(tempfile.mkdtemp(prefix="momos_"))
        paths = []
        cur = mon
        while cur <= sun:
            paths.append(export_order_csv(cur.isoformat(), tmp, tag="1",
                                          headless=not args.headed))
            cur += timedelta(days=1)
    print(f"csv files   : {len(paths)}")

    wk = compute_week(paths)
    sales, units = sum(wk["oSales"]), sum(wk["oUnits"])
    print(f"week sales  : {sales:,}  units {units:,}  orders {wk['orders']:,}")

    # ---- gates ------------------------------------------------------------
    errs = []
    if sales < 400_000:
        errs.append(f"week sales {sales:,} < 400,000 — expected ~700,000")
    zero = [n for n, v in zip(OUTLET_ORDER, wk["oSales"]) if v <= 0]
    if zero:
        errs.append(f"outlets with zero momo sales: {zero}")
    if wk["orders"] <= 0:
        errs.append("no invoices counted")
    if errs:
        print("\nSANITY FAILED — nothing written:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("sanity      : OK")

    if args.selftest:
        print("\nselftest only — nothing written.")
        return 0

    # ---- append + reconcile ----------------------------------------------
    D2 = append_week(json.loads(json.dumps(D)), wk, span)
    post = reconcile(D2)
    if post:
        print("\nRECONCILE FAILED after append — nothing written:")
        for p in post:
            print(f"  - {p}")
        return 1
    print("reconcile   : OK (11/11)")
    print(f"new totals  : sales {D2['kpi']['sales']:,} · units {D2['kpi']['units']:,} "
          f"· orders {D2['kpi']['orders']:,} · aov {D2['kpi']['aov']}")

    if args.dry_run:
        print("\ndry run — computed and reconciled, nothing written.")
        return 0

    out = render(html, D2, start, end, sun)
    PUBLIC_HTML.write_text(out, encoding="utf-8")
    shutil.copyfile(PUBLIC_HTML, ROOT_HTML)

    # Re-read from disk and reconcile again — never trust the in-memory copy.
    D3, _, _ = load_D(PUBLIC_HTML.read_text(encoding="utf-8"))
    if reconcile(D3) or D3["weekSpans"][-1] != span:
        print("\nVERIFY FAILED after write — restore with: git checkout -- "
              "public/nutriobox-momos-dashboard.html nutriobox-momos-dashboard.html")
        return 1
    print(f"written     : both copies, last week = {D3['weekSpans'][-1]}")

    if args.publish:
        subprocess.run(["git", "config", "user.email", "mayank@nutriobox.com"],
                       cwd=REPO, check=True)
        subprocess.run(["git", "config", "user.name", "Mayank"], cwd=REPO, check=True)
        subprocess.run(["git", "add", str(PUBLIC_HTML), str(ROOT_HTML)],
                       cwd=REPO, check=True)
        subprocess.run(["git", "commit", "-m",
                        f"Momos dashboard: add {span} ({sun.day} "
                        f"{MONTH_ABBR[sun.month - 1]} {sun.year}) — sales {sales}, "
                        f"units {units}, orders {wk['orders']}"], cwd=REPO, check=True)
        subprocess.run([str(PUSH_BAT)], cwd=REPO, shell=True)
        print("published   : committed + PUSH-momos.bat launched")
    else:
        print("\nNOT pushed. Run PUSH-momos.bat (or re-run with --publish).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
