"""
Repair September 2026 in the "Sales Data" sheet — fill missing boxes and fix the
Discount % — without disturbing cells that are already correct.

For each Sep date it pulls the SAME figures the daily job uses, but over plain
HTTP (fast, no browser needed to read):
    /users/load_restaurants_wise_data/   -> per-outlet totals (B..K)
    /users/load_sales_statistics/        -> net, online, Zomato/Swiggy, discount, orders
builds the canonical B..U row via daily_sheet.build_row (so formulas/formats are
identical to a normal daily write), then, on the sheet:
    * writes a cell only if it is currently EMPTY, or
    * it is column P (Discount %) and the current value differs from the correct
      (card-basis discount/(net+discount)) value.
Every write is read back through the formula bar and verified.  Nothing else is
touched, so correct per-outlet numbers you already have are left exactly as-is.

  python resync_sep.py --dry-run    read every Sep row, print what WOULD change
  python resync_sep.py              apply fills + discount fix, verify each write
  python resync_sep.py --date 2026-09-15

Requires the Google login (DELAY-LOGIN.bat) for the write pass; --dry-run needs
only the Petpooja cookie.
"""
from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

import config
from daily_sheet import (WEEKDAY_TAB, COLUMN_OUTLET, build_row, row_label,
                         _norm_daylabel, SALES_DATA_SHEET_ID)
from dashboard_scrape import _RES_NAME
from sheet_writer import BrowserWriter

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = config.PETPOOJA_BASE.rstrip("/")
# column letter for each 0-based build_row index: B=0..K=9, L=10, M=11, N=12 ... U=19
COL_LETTERS = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
               "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U"]


def _num(s) -> float:
    try:
        return float(str(s).replace(",", "").strip())
    except Exception:
        return 0.0


def _post(ep: str, d: str, cookie: str) -> dict:
    body = urllib.parse.urlencode({"from_date": d, "to_date": d}).encode()
    req = urllib.request.Request(
        BASE + ep, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "X-Requested-With": "XMLHttpRequest",
                 "Cookie": cookie, "User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return json.loads(urllib.request.urlopen(req, timeout=45, context=ctx).read().decode())


def pull(d: str, cookie: str) -> dict:
    """Assemble the same dict shape scrape_daily returns, over HTTP."""
    rw = _post("/users/load_restaurants_wise_data/", d, cookie)
    st = (_post("/users/load_sales_statistics/", d, cookie).get("Statistics_data") or {})
    by = {}
    for e in rw.get("all_restaurant_statistics", []):
        rid = e.get("res_id")
        if rid in (0, None):
            continue
        name = _RES_NAME.get(int(rid))
        if name:
            by[name] = {"total": _num(e.get("total_sales")),
                        "net": _num(e.get("net_sales")),
                        "orders": int(_num(e.get("total_orders")))}
    total_sales = _num(st.get("total_sales"))
    net = _num(st.get("t_net"))
    online = _num(st.get("t_o"))
    discount = _num(st.get("total_discount"))
    return {
        "by_outlet": by,
        "total_sales": total_sales,
        "net_sales": net,
        "online_sales": online,
        "zomato": _num(st.get("o_t_z")),
        "swiggy": _num(st.get("o_t_s")),
        "total_orders": int(_num(st.get("total_orders"))),
        "online_pct": round(online / total_sales * 100, 2) if (online and total_sales) else 0.0,
        # card-basis discount %, matches Petpooja's "% Discounts given"
        "discount_pct": round(discount / (net + discount) * 100, 2) if (net + discount) else 0.0,
    }


def sanity(data: dict, d: str) -> list[str]:
    errs = []
    by = data["by_outlet"]
    miss = [n for _, n in COLUMN_OUTLET if n not in by]
    if miss:
        errs.append(f"missing outlets from Petpooja: {miss}")
    summed = sum(by.get(n, {}).get("total", 0) for _, n in COLUMN_OUTLET)
    if data["total_sales"] and abs(summed - data["total_sales"]) > 2.0:
        errs.append(f"outlet sum {summed:,.0f} != total_sales {data['total_sales']:,.0f}")
    if not data["net_sales"] or not data["total_orders"]:
        errs.append("net or orders missing")
    return errs


def find_row(grid, label):
    want = _norm_daylabel(label)
    for idx, r in enumerate(grid, start=1):
        if r and want is not None and _norm_daylabel(r[0]) == want:
            return idx
    return None


def norm_pct(s):
    try:
        return round(_num(str(s).replace("%", "")), 2)
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="single YYYY-MM-DD (default: all Sep 2026)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.date:
        dates = [datetime.strptime(args.date, "%Y-%m-%d").date()]
    else:
        d0 = date(2026, 9, 1)
        dates = [d0 + timedelta(days=i) for i in range((date(2026, 9, 27) - d0).days + 1)]

    cookie = json.load(open(config.SECRETS / "tokens.json"))["petpooja_cookie"]

    # pull all data first (fail fast)
    payload = {}
    for d in dates:
        data = pull(d.isoformat(), cookie)
        errs = sanity(data, d.isoformat())
        if errs:
            print(f"!! {d} sanity: {errs} — skipping this date")
            continue
        payload[d] = data

    changed = {"filled": [], "fixedP": [], "verify_fail": []}
    with BrowserWriter(headless=True) as w:
        w.open_book(SALES_DATA_SHEET_ID)
        grids = {}
        for d in dates:
            if d not in payload:
                continue
            data = payload[d]
            tab = WEEKDAY_TAB[d.weekday()]
            label = row_label(d)
            w.select_tab(tab)
            if tab not in grids:
                grids[tab] = w.read_tab(tab)
            grow = find_row(grids[tab], label)
            if grow is None:
                print(f"!! {label} ({tab}): no column-A row — SKIP")
                changed["verify_fail"].append(f"{label}:norow")
                continue
            grid_row = grids[tab][grow - 1] if grow - 1 < len(grids[tab]) else []
            # verify true sheet row via formula bar, self-correct +/-1
            row = grow
            want = _norm_daylabel(label)
            if _norm_daylabel(w.read_selected_value(f"A{row}")) != want:
                fixed = None
                for cand in (row + 1, row - 1):
                    if cand >= 1 and _norm_daylabel(w.read_selected_value(f"A{cand}")) == want:
                        fixed = cand
                        break
                if fixed is None:
                    print(f"!! {label} ({tab}): row {row} label mismatch, no adjacent — SKIP")
                    changed["verify_fail"].append(f"{label}:mismatch")
                    continue
                row = fixed

            def grid_cell(letter):
                idx = ord(letter) - 65  # A=0, B=1 ...
                return (grid_row[idx] if idx < len(grid_row) else "") or ""

            values = build_row(data, row)  # 20 items, index 0..19 -> B..U
            for i, val in enumerate(values):
                col = COL_LETTERS[i]
                if col == "M":
                    continue
                cur = grid_cell(col)              # fast detection from the grid
                cur_empty = not (cur or "").strip()
                do = False
                reason = ""
                if cur_empty and str(val).strip() != "":
                    do, reason = True, "fill"
                elif col == "P" and not cur_empty:
                    if norm_pct(cur) != norm_pct(val):
                        do, reason = True, f"fixP({cur}->{val})"
                if not do:
                    continue
                if args.dry_run:
                    print(f"  ~ {label} ({tab}) {col}{row}: {reason}  [{cur!r} -> {val!r}]")
                    (changed["fixedP"] if reason.startswith("fixP") else changed["filled"]).append(f"{label}:{col}")
                    continue
                w.write_cell(f"{col}{row}", val)
                back = w.read_selected_value(f"{col}{row}")
                ok = (norm_pct(back) == norm_pct(val)) if str(val).endswith("%") else \
                     ((back or "").strip() != "")
                tag = "OK" if ok else "FAIL"
                print(f"  {tag} {label} ({tab}) {col}{row}: {reason}  read-back {back!r}")
                if not ok:
                    changed["verify_fail"].append(f"{label}:{col}")
                elif reason.startswith("fixP"):
                    changed["fixedP"].append(f"{label}:{col}")
                else:
                    changed["filled"].append(f"{label}:{col}")

    print("\n==== summary ====")
    print(f"cells filled : {len(changed['filled'])}")
    print(f"discount fix : {len(changed['fixedP'])}")
    print(f"problems     : {len(changed['verify_fail'])}  {changed['verify_fail']}")
    return 1 if changed["verify_fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
