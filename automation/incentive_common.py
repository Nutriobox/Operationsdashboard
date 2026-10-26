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

# Outlet -> sheet column (G..P), in write order. Keys are canonical short names.
# 2026-10-26: corrected H..Q -> G..P. A column was removed around August and the
# outlet headers moved one column left (confirmed: June/July are H..Q, but
# August/September/October headers and scores are G..P). The code still said H..Q,
# which — once the writer actually worked — put every score one column right of its
# outlet (it misaligned September's rows 3/15/18 before this fix).
OUTLET_COL = {
    "Rohini": "G", "KKD": "H", "Dwarka": "I", "JP": "J", "Shivalik": "K",
    "RN": "L", "Sec142": "M", "DLF": "N", "Sec15": "O", "Sec63": "P",
}
OUTLET_ORDER = ["Rohini", "KKD", "Dwarka", "JP", "Shivalik", "RN", "Sec142", "DLF", "Sec15", "Sec63"]

# Points-earned rows per metric (1-based sheet rows).
ROW = {1: 3, 2: 6, 3: 9, 4: 12, 5: 15, 6: 18, 7: 21, 8: 24}
TOTAL_ROW = 28

# Every "Points earned" row whose outlet cells (G..P) a fresh month tab must start
# blank: the 8 automated metrics plus row 27 (Café cleanliness, set manually).
POINTS_ROWS = tuple(sorted(ROW.values())) + (27,)     # 3,6,9,12,15,18,21,24,27


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
    rows = {metric_row: {outlet_short: points}}. Writes each metric row across G..P
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
        vals = [by_outlet.get(o, "") for o in OUTLET_ORDER]     # G..P
        writer.write_rows_down(f"G{metric_row}", [vals])
    # Verify by reading each written cell back.
    for metric_row, by_outlet in rows.items():
        for i, o in enumerate(OUTLET_ORDER):
            want = by_outlet.get(o, "")
            if want == "":
                continue
            col = chr(ord("G") + i)                    # G..P
            have = (writer.read_selected_value(f"{col}{metric_row}") or "").strip()
            if str(have) != str(want):
                problems.append(f"{col}{metric_row} {o}: wrote {want}, read {have!r}")
    return problems


# ---- service-account writer (native Incentive Structure sheet) -----------------
class SASheetWriter:
    """Drop-in replacement for sheet_writer.BrowserWriter, but ONLY for the
    Incentive Structure sheet — which is a native Google Sheet, so it is written
    straight through the Sheets API with the service-account key. No browser, no
    Google login, and no flaky canvas read-back (the three things that made the
    old UI writer fail or, worse, write to the wrong place). Implements just the
    methods the incentive entry scripts call when they open the INCENTIVE sheet:
    open_book / tab_titles / select_tab / duplicate_tab / write_rows_down /
    read_selected_value. (2026-10-26)
    """

    def __init__(self):
        self._api = None
        self._sid = None
        self._tab = None

    def __enter__(self):
        from sheets import Sheets
        self._api = Sheets()
        return self

    def __exit__(self, *exc):
        return False

    def open_book(self, sheet_id: str):
        self._sid = sheet_id

    def tab_titles(self):
        return self._api.tab_titles(self._sid)

    def duplicate_tab(self, source_title: str, new_title: str, index: int = 0):
        self._api.duplicate_tab(self._sid, source_title, new_title, index)

    def select_tab(self, title: str):
        self._tab = title

    def write_rows_down(self, top_left: str, rows):
        from sheets import a1
        self._api.write_range(self._sid, a1(self._tab, top_left), rows)

    def read_selected_value(self, ref: str) -> str:
        from sheets import a1
        vals = self._api.read_range(self._sid, a1(self._tab, ref))
        return "" if not vals or not vals[0] else str(vals[0][0])

    def ensure_month_tab(self, new_title: str) -> bool:
        """Create the month tab if it is missing and return True if created.

        The sheet has no blank 'Sheet1'/'Template' tab to copy (tabs are month
        names only), so a new month is made by duplicating the newest month tab
        for its structure, then CLEARING the outlet score cells (G..P) on every
        points-earned row — so the month starts empty instead of inheriting the
        previous month's scores. Labels, bands, headers and the totals row are
        left intact. (2026-10-26: replaces the old duplicate_tab('Sheet1', ...)
        in the monthly run, which referenced a tab that no longer exists.)
        """
        from sheets import a1
        if new_title in self.tab_titles():
            return False
        src = self.tab_titles()[0]            # newest month tab is leftmost
        self.duplicate_tab(src, new_title, 0)
        self._api.api.values().batchClear(
            spreadsheetId=self._sid,
            body={"ranges": [a1(new_title, f"G{r}:P{r}") for r in POINTS_ROWS]},
        ).execute()
        return True
