"""
Shared helpers for the three NutrioBox Outlet-Incentive fills (ports of the Claude
tasks incentive--monthly-metrics, incentive--weekly-metrics, incentive-delay-metrics).

All three write "Points earned" (0-4) per outlet into the Incentive Structure sheet,
one metric per row, outlets across columns H..Q. This module holds the parts they
share: the outlet->column map, the EXACT scoring bands (transcribed from the task
SKILLs — this is the deterministic core and must stay correct), month-tab resolution,
and a write+read-back helper on top of sheet_writer.BrowserWriter.

Nothing here scrapes a portal; the per-metric data readers live in the entry scripts
(incentive_monthly.py / incentive_weekly.py / incentive_delay.py).
"""
from __future__ import annotations

from datetime import date, timedelta

import config
from sheet_writer import BrowserWriter, WriteError

INCENTIVE_SHEET_ID = "1-eNd2ygcQdR7nw_a1uA_TDH4_TbEzdt1P__IjP46S8Q"

# Outlet -> sheet column (H..Q), in write order. Keys are canonical short names.
OUTLET_COL = {
    "Rohini": "H", "KKD": "I", "Dwarka": "J", "JP": "K", "Shivalik": "L",
    "RN": "M", "Sec142": "N", "DLF": "O", "Sec15": "P", "Sec63": "Q",
}
OUTLET_ORDER = ["Rohini", "KKD", "Dwarka", "JP", "Shivalik", "RN", "Sec142", "DLF", "Sec15", "Sec63"]

# Points-earned rows per metric (1-based sheet rows).
ROW = {1: 3, 2: 6, 3: 9, 4: 12, 5: 15, 6: 18, 7: 21, 8: 24}
TOTAL_ROW = 28


def _band(value, ladder, higher_is_better=True):
    """ladder = list of (threshold, points) evaluated in order; returns points for value.
    Each entry means: for higher_is_better, value >= threshold -> points (descending
    thresholds); for lower_is_better, value <= threshold -> points (ascending)."""
    for thr, pts in ladder:
        if (higher_is_better and value >= thr) or (not higher_is_better and value <= thr):
            return pts
    return ladder[-1][1]


# ---- EXACT scoring bands from the SKILLs (do not "tidy" the numbers) -----------
def score_m1_saleperday_pct(pct: float) -> int:
    """Metric 1: avg sale/day vs prev month %. NOTE: SKILL leaves pct==0 undefined
    (bands are pct<0 ->1 and pct>0 ->2); we map exactly 0 to 1 (no growth)."""
    if pct < -2: return 0
    if pct < 0:  return 1          # -2 <= pct < 0
    if pct == 0: return 1          # SKILL gap; treated as no-growth
    if pct <= 3: return 2
    if pct <= 5: return 3
    return 4                        # pct > 5 (SKILL: 5-7 ->4 and >7 ->4)


def score_m2_rating(r: float) -> int:
    if r < 4.0: return 0
    if r < 4.3: return 1
    if r < 4.5: return 2
    if r <= 4.8: return 3
    return 4


def score_m3_delay15(p: float) -> int:   # lower is better
    if p > 30: return 0
    if p > 20: return 1
    if p > 15: return 2
    if p > 10: return 3
    return 4


def score_m4_delay25(p: float) -> int:   # lower is better
    if p > 10: return 0
    if p > 8:  return 1
    if p > 5:  return 2
    if p > 1:  return 3
    return 4


def score_m5_delivery_pct(p: float) -> int:  # lower is better
    if p > 75: return 0
    if p > 73: return 1
    if p > 70: return 2
    if p > 68: return 3
    return 4


def score_m6_aov(aov: float, bands=None) -> int:
    """Metric 6: AOV. Default bands from the SKILL ("<480=0 ... >570=4"); the tab's
    row-17 labels are authoritative — pass bands=[(thr,pts),...] read at runtime.
    VALIDATE: confirm the intermediate cut points on the current tab (only <480 and
    >570 are stated explicitly in the SKILL)."""
    if bands:
        return _band(aov, bands, higher_is_better=True)
    if aov < 480: return 0
    if aov < 510: return 1
    if aov < 540: return 2
    if aov <= 570: return 3
    return 4


def score_m7_captain(p: float) -> int:
    if p < 93: return 0
    if p < 95: return 1
    if p < 98: return 2
    if p <= 99.9: return 3
    return 4


def score_m8_feedback(p: float) -> int:
    if p < 83: return 0
    if p < 85: return 1
    if p < 88: return 2
    if p < 90: return 3
    return 4


# ---- month-tab label -----------------------------------------------------------
def month_tab_label(d: date) -> str:
    """The Incentive Structure sheet names its tabs by month name only —
    confirmed 2026-09-08 the tabs are 'August', 'July', 'June' (no year)."""
    return d.strftime("%B")


def last_completed_week(today: date):
    """(Mon, Sun) of the most recently completed Mon-Sun week."""
    this_mon = today - timedelta(days=today.weekday())
    mon = this_mon - timedelta(days=7)
    return mon, mon + timedelta(days=6)


# ---- write helper --------------------------------------------------------------
def write_metric_rows(writer: BrowserWriter, tab: str, rows: dict[int, dict[str, int]],
                      require_tab: bool = True) -> list[str]:
    """
    rows = {metric_row: {outlet_short: points}}. Writes each metric row across H..Q
    in OUTLET_ORDER, then reads the row back and checks it. Returns problems (empty
    == OK). Never creates a tab here; caller decides whether to duplicate the
    template (the monthly run owns tab creation).
    """
    problems = []
    if tab not in writer.tab_titles():
        if require_tab:
            return [f"tab {tab!r} does not exist — the monthly run creates it; refusing to create here"]
    writer.select_tab(tab)
    for metric_row, by_outlet in rows.items():
        vals = [by_outlet.get(o, "") for o in OUTLET_ORDER]     # H..Q
        writer.write_rows_down(f"H{metric_row}", [vals])
    # Verify via the LIVE formula bar per cell (Name Box navigation is reliable; the
    # gviz read-back grid does NOT line up with true sheet rows on this workbook, so a
    # grid-index check false-fails even when the write is correct).
    for metric_row, by_outlet in rows.items():
        for i, o in enumerate(OUTLET_ORDER):
            want = by_outlet.get(o, "")
            if want == "":
                continue
            col = chr(ord("H") + i)                    # H..Q
            have = (writer.read_selected_value(f"{col}{metric_row}") or "").strip()
            if str(have) != str(want):
                problems.append(f"{col}{metric_row} {o}: wrote {want}, read {have!r}")
    return problems
