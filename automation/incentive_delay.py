"""
Incentive — WEEKLY DELAY metrics (Wed) -> Playwright port of the Claude
"incentive-delay-metrics-weekly-wed" task.

Scores Metric 3 (% online orders delayed >15 min) and Metric 4 (>25 min) for the
most recently completed week and writes rows 9 and 12 (H..Q) of the scored-month tab
in the Incentive Structure sheet. Overwrites those two rows each week.

    python incentive_delay.py --selftest             # read + score, WRITE NOTHING
    python incentive_delay.py --dry-run              # + preview the row, no write
    python incentive_delay.py --dry-run --monday 2026-08-31
    python incentive_delay.py --headed               # visible browser
    python incentive_delay.py                         # live (last completed week)

VALIDATE BEFORE SCHEDULING (needs the live signed-in session):
  * DELAY SOURCE: the SKILL reads the delay dashboard's "All Outlets Comparison —
    Latest Week" Chart.js datasets "U: % >15 min" and "W: % >25 min". This port reads
    the same U/W per outlet from the Weekly Sales sheet's latest weekly tab (the data
    behind that chart) via gviz. CONFIRM the sheet's U/W columns are the ">15"/">25"
    series (they are labelled as 15-25 / 26+ bands in the weekly-report layout — if
    those are DIFFERENT numbers from the dashboard, read the dashboard chart instead).
  * Confirm the scored-month tab exists (this job does NOT create it).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

import incentive_common as inc
import config

IST = timezone(timedelta(hours=5, minutes=30))

# Source: the PUBLIC delay dashboard HTML on Supabase. It embeds
#   const data = { "<outlet>": [ [T,U,V,W] per week, ... ], ... }
# where each week row is [count>15, %>15 (U), count>25, %>25 (W)]; the LAST row is
# the latest completed week (the "All Outlets Comparison - Latest Week" chart).
# Confirmed 2026-09-08 against the live Chart.js (DLF last row [266,35.7,31,4.16]).
DELAY_HTML_URL = config.SUPABASE_PUBLIC + "/delay-dashboard.html"

# delay-dashboard outlet label -> incentive short.
def _short_for(label: str):
    t = (label or "").strip().lower()
    if "142" in t or "advant" in t:
        return "Sec142"
    if "noida 63" in t or "sector 63" in t:
        return "Sec63"
    if "sector 15" in t or "ggn" in t:
        return "Sec15"
    if "dlf" in t: return "DLF"
    if "rajinder" in t: return "RN"
    if "dwarka" in t: return "Dwarka"
    if "janakpuri" in t: return "JP"
    if "karkardooma" in t: return "KKD"
    if "rohini" in t: return "Rohini"
    if "shivalik" in t: return "Shivalik"
    return None


def _extract_const_data(html: str) -> dict:
    """Pull `const data = {...}` out of the delay HTML and JSON-parse it."""
    import json
    i = html.find("const data")
    b = html.find("{", i)
    depth = 0
    for j in range(b, len(html)):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[b:j + 1])
    raise RuntimeError("delay HTML: could not extract const data object")


def read_delay_week(monday: date, sunday: date, headless: bool = True) -> dict:
    """
    Return {short: (u_pct, w_pct)} for the latest completed week, parsed from the
    PUBLIC delay dashboard HTML (no login/browser needed). Raises if any outlet is
    missing so a partial week never scores.
    """
    import re
    import requests
    html = requests.get(DELAY_HTML_URL, timeout=30).text
    # capture the dashboard's own "Latest Week (Aug 24 - Aug 30)" so the caller scores
    # the week the dashboard ACTUALLY has (it's the source of truth, not the cron day).
    m = re.search(r"Latest Week \(([^)]+)\)", html)
    globals()["LATEST_WEEK_LABEL"] = m.group(1) if m else None
    data = _extract_const_data(html)
    out = {}
    for label, rows in data.items():
        short = _short_for(label)
        if not short or not rows:
            continue
        last = rows[-1]                      # [count>15, %>15, count>25, %>25]
        out[short] = (float(last[1]), float(last[3]))
    missing = [o for o in inc.OUTLET_ORDER if o not in out]
    if missing:
        raise RuntimeError(f"delay: missing outlets {missing} — refusing to score partial")
    return out


LATEST_WEEK_LABEL = None
_MONTHS3 = {m[:3].lower(): m for m in
            ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]}


def _scored_month_from_label(label: str):
    """'Aug 24 - Aug 30' -> 'August' (month the week ENDS in)."""
    if not label:
        return None
    end = label.split("-")[-1].strip()          # 'Aug 30'
    tok = end.split()[0][:3].lower()
    return _MONTHS3.get(tok)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--monday", help="week's Monday YYYY-MM-DD (default: last completed week)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    headless = not args.headed

    if args.monday:
        mon = datetime.strptime(args.monday, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            print(f"ERROR: --monday {args.monday} is a {mon.strftime('%A')}, not a Monday.")
            return 2
        sun = mon + timedelta(days=6)
    else:
        mon, sun = inc.last_completed_week(datetime.now(IST).date())
    delay = read_delay_week(mon, sun, headless)
    # The dashboard's published latest week is the source of truth for BOTH the data
    # and the target month tab — this avoids scoring stale data into a not-yet-created
    # month (e.g. running before the Wed delay publish).
    dash_month = _scored_month_from_label(LATEST_WEEK_LABEL)
    tab = dash_month or inc.month_tab_label(sun)
    print(f"requested   : {mon} .. {sun}")
    print(f"dashboard wk: {LATEST_WEEK_LABEL!r}  -> month tab {tab!r}")
    if dash_month and dash_month != inc.month_tab_label(sun):
        print(f"NOTE: scoring the dashboard's published week ({LATEST_WEEK_LABEL}), "
              f"not the requested week's month — the dashboard is the source of truth.")
    m3 = {o: inc.score_m3_delay15(delay[o][0]) for o in inc.OUTLET_ORDER}
    m4 = {o: inc.score_m4_delay25(delay[o][1]) for o in inc.OUTLET_ORDER}

    for o in inc.OUTLET_ORDER:
        u, wv = delay[o]
        print(f"  {o:<8} U(>15)={u:>5} -> M3={m3[o]}   W(>25)={wv:>5} -> M4={m4[o]}")

    if args.selftest or args.dry_run:
        print("\n(dry) nothing written.")
        return 0

    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(inc.INCENTIVE_SHEET_ID)
        problems = inc.write_metric_rows(w, tab, {inc.ROW[3]: m3, inc.ROW[4]: m4})
    if problems:
        print("\nVERIFY FAILED — check the sheet:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"\nOK — wrote rows {inc.ROW[3]} & {inc.ROW[4]} (H..Q) on {tab!r}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
