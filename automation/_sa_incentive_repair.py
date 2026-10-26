"""
One-off repair of September rows 3/15/18 (M1/M5/M6) on the Incentive Structure
sheet, run THROUGH the newly-migrated service-account write path so it doubles as
an end-to-end check of that path.

Background: the 2026-10-26 11:32 incentive_monthly run wrote these three rows to
H..Q (old, wrong columns) instead of G..P, shifting every outlet's score one cell
right and leaving a stray value in Q. These are the exact per-outlet M1/M5/M6
values that run printed; we rewrite them correctly to G..P and clear the Q strays.
"""
import incentive_common as inc
from sheets import a1

TAB = "September"

# OUTLET_ORDER = Rohini, KKD, Dwarka, JP, Shivalik, RN, Sec142, DLF, Sec15, Sec63
M1 = [4, 4, 3, 2, 0, 4, 4, 4, 4, 0]   # row 3  (avg sale/day vs prev month)
M5 = [2, 1, 4, 2, 0, 1, 4, 0, 4, 4]   # row 15 (% sale from Delivery)
M6 = [1, 1, 3, 2, 1, 2, 3, 1, 1, 0]   # row 18 (AOV)


def by(vals):
    return dict(zip(inc.OUTLET_ORDER, vals))


def main():
    rows = {inc.ROW[1]: by(M1), inc.ROW[5]: by(M5), inc.ROW[6]: by(M6)}  # 3, 15, 18
    print("Before:")
    with inc.SASheetWriter() as w:
        w.open_book(inc.INCENTIVE_SHEET_ID)
        w.select_tab(TAB)
        for r in (3, 15, 18):
            print(f"  row{r:>2} G..Q:", w._api.read_range(inc.INCENTIVE_SHEET_ID, a1(TAB, f"G{r}:Q{r}")))

        problems = inc.write_metric_rows(w, TAB, rows, require_tab=True)
        # clear the stray Q cells left by the old H..Q write
        for r in (inc.ROW[1], inc.ROW[5], inc.ROW[6]):
            w._api.api.values().clear(
                spreadsheetId=inc.INCENTIVE_SHEET_ID, range=a1(TAB, f"Q{r}"), body={}
            ).execute()

    print("\nwrite_metric_rows problems (empty == OK):", problems)

    print("\nAfter:")
    with inc.SASheetWriter() as w:
        w.open_book(inc.INCENTIVE_SHEET_ID)
        w.select_tab(TAB)
        for r in (3, 15, 18):
            print(f"  row{r:>2} G..Q:", w._api.read_range(inc.INCENTIVE_SHEET_ID, a1(TAB, f"G{r}:Q{r}")))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
