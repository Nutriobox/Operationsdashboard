"""Read the Claude twin's existing D..W + AS..AU for Sep 7-13 from the weekly
sheet, so we can diff against the Playwright dry-run. WRITES NOTHING.
Output -> C:\\Users\\hp\\Downloads\\weekly-compare-out.txt"""
from __future__ import annotations
import sys
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import weekly_report as W
from sheet_writer import BrowserWriter

TAB = "Sep 7 - Sep 13, 2026"
OUT = Path(r"C:\Users\hp\Downloads\weekly-compare-out.txt")
lines=[]
def log(*a): lines.append(" ".join(str(x) for x in a))

def main():
    with BrowserWriter(headless=True) as w:
        w.open_book(W.WEEKLY_REPORT_SHEET_ID)
        grid = w.read_tab(TAB)
    log(f"TWIN values in tab {TAB!r} (rows read: {len(grid)}):")
    for key,row,*_ in W.OUTLETS:
        r = grid[row-1] if len(grid)>=row else []
        dw = r[3:23] if len(r)>=23 else r[3:]     # D..W
        asu = r[44:47] if len(r)>=47 else []       # AS..AU
        log(f"  row {row:>2} {key:<11} D..W={dw[:6]}...{dw[-2:] if len(dw)>=2 else dw}  AS..AU={asu}")

try: main()
finally:
    OUT.write_text("\n".join(lines), encoding="utf-8"); print("wrote", OUT)
