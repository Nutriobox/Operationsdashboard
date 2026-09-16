"""
Incentive — WEEKLY metrics (every Monday) -> Playwright port of the Claude
"incentive--weekly-metrics-first-monday" task.

Scores the most recently completed week and fills rows 6, 9, 12, 21, 24 (H..Q) of the
scored-month tab in the Incentive Structure sheet:
    row 6  Metric 2  Avg rating          (ratings dashboard / Supabase ratings history)
    row 9  Metric 3  % delay >15 min     (delay week — reused from incentive_delay)
    row 12 Metric 4  % delay >25 min     (delay week — reused from incentive_delay)
    row 21 Metric 7  Captain-App coverage (Weekly KOT sheet, column D)
    row 24 Metric 8  Feedback rate       (feedback dashboard)
Sec 63 (cloud kitchen) scores 0 on Metrics 7 and 8.

    python incentive_weekly.py --selftest / --dry-run / --headed / (live)

VALIDATE BEFORE SCHEDULING (needs the live session):
  * M2 ratings: confirm the per-outlet weekly avg source. Supabase
    reports/ratings-history.json is the natural feed — CONFIRM its shape (weekStart
    key + per-outlet combined Zomato+Swiggy+Google avg) then finish read_ratings().
  * M8 feedback: confirm the feedback dashboard's per-outlet "Feedback Rate" data
    source, then finish read_feedback(). (SKILL notes most outlets currently score 0.)
  * M3/M4 reuse incentive_delay.read_delay_week — see its VALIDATE note on U/W.
  * M7 captain: confirm the Weekly KOT tab name + that column D is coverage %.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

import config
import incentive_common as inc
from incentive_delay import read_delay_week

IST = timezone(timedelta(hours=5, minutes=30))

# Weekly KOT sheet label -> incentive short (Metric 7, column D coverage).
KOT_LABEL_TO_SHORT = {
    "dlf": "DLF", "rajinder": "RN", "dwarka": "Dwarka", "janakpuri": "JP",
    "karkardooma": "KKD", "noida": "Sec142", "prashant vihar": "Rohini",
    "sector 15": "Sec15", "shivalik": "Shivalik",
    # Prashant Vihar must win over a bare "noida" match, so check it first (below).
}


def _kot_short(label: str):
    t = (label or "").strip().lower()
    if "prashant" in t:
        return "Rohini"
    if "sector 15" in t or "gurugram" in t:
        return "Sec15"
    for frag, short in KOT_LABEL_TO_SHORT.items():
        if frag in t:
            return short
    return None


def read_captain(monday: date, sunday: date, headless: bool) -> dict:
    """Metric 7: Captain-App Coverage % per outlet from the Weekly KOT sheet, col D."""
    from sheet_writer import BrowserWriter
    tab = f"{inc_ord(monday.day)} {monday.strftime('%B')} - {inc_ord(sunday.day)} {sunday.strftime('%B')}"
    with BrowserWriter(headless=headless) as w:
        w.open_book(config.KOT_WEEKLY_SHEET_ID)
        if tab not in w.tab_titles():
            raise RuntimeError(f"captain: Weekly KOT tab {tab!r} not found")
        grid = w.read_tab(tab)
    out = {}
    for row in grid:
        if not row or not row[0].strip():
            continue
        short = _kot_short(row[0])
        if not short:
            continue
        try:
            out[short] = float(str(row[3]).replace("%", "").replace(",", ""))   # col D
        except (ValueError, IndexError):
            continue
    out["Sec63"] = 0.0   # cloud kitchen — not in KOT sheet, scores 0 on M7
    return out


def inc_ord(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


RATING_NAME_TO_SHORT = {
    "prashant vihar": "Rohini", "rohini": "Rohini", "janakpuri": "JP",
    "karkardooma": "KKD", "dwarka": "Dwarka", "shivalik": "Shivalik",
    "rajinder": "RN", "advant": "Sec142", "dlf": "DLF",
    "sector 15": "Sec15", "sector 63": "Sec63",
}


def _rating_short(name: str):
    # ratings.json names (confirmed 2026-09-08): "Rohini (Prashant Vihar)", "Janakpuri",
    # "Karkardooma", "Dwarka (Sector 6)", "Malviya Nagar (Shivalik)", "Noida Sector 142",
    # "Rajinder Nagar", "Noida Sector 63", "Gurgaon DLF Phase 2", "Gurgaon Sector 15".
    t = (name or "").lower()
    if "prashant" in t or "rohini" in t:
        return "Rohini"
    if "142" in t:
        return "Sec142"
    if "sector 63" in t or "noida sector 63" in t:
        return "Sec63"
    if "sector 15" in t:
        return "Sec15"
    if "shivalik" in t:
        return "Shivalik"
    if "dlf" in t:
        return "DLF"
    if "dwarka" in t:
        return "Dwarka"
    if "karkardooma" in t:
        return "KKD"
    if "janakpuri" in t:
        return "JP"
    if "rajinder" in t:
        return "RN"
    return None


def read_ratings(monday: date, sunday: date) -> dict:
    """Metric 2: per-outlet combined avg rating (mean of zomato/swiggy/google) for the
    scored week. Reads Supabase reports/ratings-history.json (PUBLIC — no session
    needed); falls back to the current ratings.json if the week isn't in history yet.
    Shape confirmed 2026-09-08: {weeks:[{weekStart,weekEnd,outlets:[{name,zomato:{rating},
    swiggy:{rating},google:{rating}}]}]}."""
    import requests
    base = config.SUPABASE_PUBLIC
    hist = requests.get(f"{base}/ratings-history.json", timeout=30).json()
    want = monday.isoformat()
    week = next((w for w in hist.get("weeks", []) if w.get("weekStart") == want), None)
    outlets = week["outlets"] if week else \
        requests.get(f"{base}/ratings.json", timeout=30).json().get("outlets", [])
    out = {}
    for o in outlets:
        short = _rating_short(o.get("name", ""))
        if not short:
            continue
        vals = [o.get(p, {}).get("rating") for p in ("zomato", "swiggy", "google")]
        vals = [v for v in vals if isinstance(v, (int, float))]
        if vals:
            out[short] = round(sum(vals) / len(vals), 3)
    missing = [x for x in inc.OUTLET_ORDER if x not in out]
    if missing:
        raise RuntimeError(f"ratings: missing outlets {missing} — refusing to score partial")
    return out


def read_feedback(monday: date, sunday: date, headless: bool) -> dict:
    """Metric 8: per-outlet feedback rate % (= feedback ÷ dining-KOT × 100) for the
    scored week. Points: p<83->0 ... p>=90->4.

    PLACEHOLDER (2026-09-08): returns 0 for every outlet. Feedback volume is currently
    a handful of submissions against thousands of Dine-In+Pickup KOT orders, so every
    outlet's rate is far below the 83% floor -> all score 0 (matches the live feedback
    dashboard and the task SKILL's "most outlets score 0"). The real per-outlet feedback
    COUNT lives embedded in feedback-dashboard.html (a minified app, no API); the
    denominator (Dine-In+Pickup KOT) is already read for M7.
    TODO/VALIDATE: when feedback volume grows enough that any outlet could approach 83%,
    wire the real feedback count (parse feedback-dashboard.html or read the rendered
    /dashboard/feedback cards) and divide by the KOT total. Until then this is accurate."""
    return {o: 0.0 for o in inc.OUTLET_ORDER}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--monday")
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
    tab = inc.month_tab_label(sun)
    print(f"scored week : {mon} .. {sun}\nmonth tab   : {tab!r}")

    ratings = read_ratings(mon, sun)                       # M2  (raises until wired)
    delay = read_delay_week(mon, sun, headless)            # M3/M4
    captain = read_captain(mon, sun, headless)             # M7
    feedback = read_feedback(mon, sun, headless)           # M8  (raises until wired)

    m2 = {o: inc.score_m2_rating(ratings[o]) for o in inc.OUTLET_ORDER}
    m3 = {o: inc.score_m3_delay15(delay[o][0]) for o in inc.OUTLET_ORDER}
    m4 = {o: inc.score_m4_delay25(delay[o][1]) for o in inc.OUTLET_ORDER}
    m7 = {o: (0 if o == "Sec63" else inc.score_m7_captain(captain[o])) for o in inc.OUTLET_ORDER}
    m8 = {o: (0 if o == "Sec63" else inc.score_m8_feedback(feedback[o])) for o in inc.OUTLET_ORDER}

    rows = {inc.ROW[2]: m2, inc.ROW[3]: m3, inc.ROW[4]: m4, inc.ROW[7]: m7, inc.ROW[8]: m8}
    for o in inc.OUTLET_ORDER:
        print(f"  {o:<8} M2={m2[o]} M3={m3[o]} M4={m4[o]} M7={m7[o]} M8={m8[o]}")

    if args.selftest or args.dry_run:
        print("\n(dry) nothing written.")
        return 0

    from sheet_writer import BrowserWriter
    with BrowserWriter(headless=headless) as w:
        w.open_book(inc.INCENTIVE_SHEET_ID)
        if tab not in w.tab_titles():
            src = w.tab_titles()[0]          # newest month tab is leftmost
            print(f"month tab {tab!r} missing — duplicating {src!r} to create it "
                  "(monthly run then owns rows 3/15/18)")
            w.duplicate_tab(src, tab)
        problems = inc.write_metric_rows(w, tab, rows, require_tab=False)
    if problems:
        print("\nVERIFY FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"\nOK — wrote rows 6/9/12/21/24 (H..Q) on {tab!r}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
