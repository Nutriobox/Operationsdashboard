"""
One-off corrector for the Discount % column (P) of the "Sales Data" sheet.

Why: after Petpooja's 2026-09 dashboard redesign, dashboard_scrape switched to
computing discount_pct = total_discount / total_sales.  Petpooja's own
"% Discounts given" card (and every pre-Sep value in this sheet) uses
total_discount / (net_sales + total_discount)  ==  total_discount / c_t,
which is ~3-4 points lower.  This rewrites column P for the given September
dates with the correct (card) value.  dashboard_scrape.py is already fixed for
future runs; this only repairs the days already written with the wrong base.

  python fix_discount_pct.py --dry-run     locate rows + show old->new, write nothing
  python fix_discount_pct.py               live: overwrite P, read each back to verify
  python fix_discount_pct.py --date 2026-09-13

Only column P is touched.  A row is skipped (never written) unless column B..K
already carry data, so an empty row (e.g. an unfilled day) is left for
daily_sheet to fill in full.  Each write is read back through the formula bar
and compared before the script calls it done.
"""
from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

import config
from daily_sheet import WEEKDAY_TAB, row_label, _norm_daylabel, SALES_DATA_SHEET_ID
from sheet_writer import BrowserWriter

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STAT_EP = config.PETPOOJA_BASE.rstrip("/") + "/users/load_sales_statistics/"


def _num(s) -> float:
    try:
        return float(str(s).replace(",", "").strip())
    except Exception:
        return 0.0


def petpooja_discount_pct(d: str, cookie: str) -> tuple[float, float, float]:
    """Return (discount, net, pct) for a single YYYY-MM-DD, card-basis pct."""
    body = urllib.parse.urlencode({"from_date": d, "to_date": d}).encode()
    req = urllib.request.Request(
        STAT_EP, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "X-Requested-With": "XMLHttpRequest",
                 "Cookie": cookie, "User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    raw = urllib.request.urlopen(req, timeout=45, context=ctx).read().decode()
    st = json.loads(raw).get("Statistics_data") or {}
    discount = _num(st.get("total_discount"))
    net = _num(st.get("t_net"))
    base = net + discount
    pct = round(discount / base * 100, 2) if base else 0.0
    return discount, net, pct


def find_row(grid: list[list[str]], label: str) -> int | None:
    """1-based row whose column A matches `label` (day+month). None if absent.
    Unlike daily_sheet.find_target_row this does NOT require the row to be empty
    (we are deliberately overwriting one existing cell)."""
    want = _norm_daylabel(label)
    for idx, r in enumerate(grid, start=1):
        if r and want is not None and _norm_daylabel(r[0]) == want:
            return idx
    return None


def row_has_data(grid: list[list[str]], row: int) -> bool:
    """True if B..K (indices 1..10) on that 1-based row carry any value."""
    r = grid[row - 1] if 1 <= row <= len(grid) else []
    return any((c or "").strip() for c in r[1:11])


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="single date YYYY-MM-DD (default: all of Sep 2026)")
    ap.add_argument("--dry-run", action="store_true",
                    help="locate rows + preview old->new, write nothing")
    args = ap.parse_args()

    if args.date:
        from datetime import datetime
        dates = [datetime.strptime(args.date, "%Y-%m-%d").date()]
    else:
        dates = list(daterange(date(2026, 9, 1), date(2026, 9, 27)))

    tok = json.load(open(config.SECRETS / "tokens.json"))
    cookie = tok["petpooja_cookie"]

    # Pull correct percentages first (fail fast if Petpooja is unreachable).
    plan = []  # (date, tab, label, discount, net, pct)
    for d in dates:
        discount, net, pct = petpooja_discount_pct(d.isoformat(), cookie)
        plan.append((d, WEEKDAY_TAB[d.weekday()], row_label(d), discount, net, pct))
        print(f"{d.isoformat()}  {WEEKDAY_TAB[d.weekday()]:5} {row_label(d):16} "
              f"disc={discount:12,.2f} net={net:12,.2f} -> {pct:.2f}%")

    fixed, skipped, missing = [], [], []
    with BrowserWriter(headless=True) as w:
        w.open_book(SALES_DATA_SHEET_ID)
        grids: dict[str, list[list[str]]] = {}
        for d, tab, label, discount, net, pct in plan:
            w.select_tab(tab)
            if tab not in grids:
                grids[tab] = w.read_tab(tab)
            grid = grids[tab]
            row = find_row(grid, label)
            if row is None:
                print(f"  ! {label} ({tab}): no column-A row found — SKIP")
                missing.append(label)
                continue
            # verify against the live formula bar, self-correct +/-1
            want = _norm_daylabel(label)
            if _norm_daylabel(w.read_selected_value(f"A{row}")) != want:
                corr = None
                for cand in (row + 1, row - 1):
                    if cand >= 1 and _norm_daylabel(w.read_selected_value(f"A{cand}")) == want:
                        corr = cand
                        break
                if corr is None:
                    print(f"  ! {label} ({tab}): row {row} label mismatch and no "
                          f"adjacent match — SKIP (won't risk wrong row)")
                    missing.append(label)
                    continue
                row = corr
            if not row_has_data(grid, row):
                print(f"  · {label} ({tab}) row {row}: B..K empty — SKIP "
                      f"(let daily_sheet fill the whole row)")
                skipped.append(label)
                continue

            new_val = f"{pct:.2f}%"
            old_val = w.read_selected_value(f"P{row}")
            if args.dry_run:
                print(f"  ~ {label} ({tab}) P{row}: {old_val!r} -> {new_val!r} (dry-run)")
                continue
            w.write_cell(f"P{row}", new_val)
            back = w.read_selected_value(f"P{row}")
            ok = back.replace(" ", "").rstrip("%") == new_val.rstrip("%") or \
                 abs(_num(back.rstrip("%")) - pct) < 0.005
            print(f"  {'OK' if ok else 'FAIL'} {label} ({tab}) P{row}: "
                  f"{old_val!r} -> wrote {new_val!r}, read back {back!r}")
            (fixed if ok else missing).append(label)

    print(f"\nfixed={len(fixed)}  skipped(empty)={len(skipped)}  problems={len(missing)}")
    if skipped:
        print(f"  empty rows left for daily_sheet: {skipped}")
    if missing:
        print(f"  NEEDS ATTENTION: {missing}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
