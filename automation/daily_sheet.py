"""
Daily Dashboard → Playwright (port of the Cowork task `petpooja-sales-to-gsheet`).

Fills yesterday's row in the day-of-week tab of the "Sales Data" sheet from the
Petpooja POS dashboard. No Claude tokens; runs unattended.

    python daily_sheet.py --selftest              # reads only, writes nothing
    python daily_sheet.py --dry-run               # full pull + row preview
    python daily_sheet.py --dry-run --date 2026-08-26
    python daily_sheet.py --headed                # live, visible browser
    python daily_sheet.py                         # live (scheduled mode)

Pipeline (mirrors the SKILL exactly):
    resolve target date -> tab (Mon/Tues/Wed/Thur/Fri/Sat/Sun) + "26th August"
    -> scrape POS dashboard for that date (Playwright)
    -> sanity gates
    -> locate the target row by its column-A date label
    -> write B..U in one pass
    -> fix O (percent) and S (integer format)
    -> read back through gviz and compare

Guards, in order of how badly they bite:
  A. The scraper refuses to read unless the picker really shows the target date.
  B. The target row is accepted only if column A already carries the expected
     "26th August" label AND B..U are empty. We never "write to the next empty
     row" blindly — that is how a bank holiday silently shifts a month.
  C. The 10 outlet totals must sum to Total Sales (±1) before anything is typed.
  D. Every written value is read back through gviz and compared.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta

import config
from dashboard_scrape import scrape_daily
from petpooja import SessionExpired
from sheet_writer import BrowserWriter

SALES_DATA_SHEET_ID = config.SALES_DATA_SHEET_ID

# Tab names use 4-letter abbreviations for Tue/Thu — the sheet's own spelling.
WEEKDAY_TAB = {0: "Mon", 1: "Tues", 2: "Wed", 3: "Thur",
               4: "Fri", 5: "Sat", 6: "Sun"}

# Column -> Petpooja outlet name. G vs K is the classic mix-up: G is plain
# "NutrioBox (Noida)" (Noida Advant), K is "NutrioBox ( Sector 63 Noida )".
COLUMN_OUTLET = [
    ("B", "NutrioBox (Prashant Vihar)"),      # sheet header: Rohini
    ("C", "NutrioBox (Janakpuri)"),
    ("D", "NutrioBox (Karkardooma)"),
    ("E", "NutrioBox (Dwarka)"),
    ("F", "NutrioBox (Shivalik)"),
    ("G", "NutrioBox (Noida)"),               # Noida Advant
    ("H", "NutrioBox ( Rajinder Nagar)"),
    ("I", "NutrioBox ( DLF Phase 2)"),
    ("J", "NutrioBox (Sector 15, Gurugram)"),
    ("K", "NutrioBox ( Sector 63 Noida )"),
]


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def row_label(d: date) -> str:
    """Column-A label, e.g. '26th August'."""
    return f"{ordinal(d.day)} {d.strftime('%B')}"


def resolve_target(arg: str | None) -> date:
    if arg:
        return datetime.strptime(arg, "%Y-%m-%d").date()
    return date.today() - timedelta(days=1)


# ---------------------------------------------------------------------------
# Sanity gates
# ---------------------------------------------------------------------------
def sanity(data: dict) -> list[str]:
    errs: list[str] = []
    by = data.get("by_outlet") or {}

    missing = [name for _, name in COLUMN_OUTLET if name not in by]
    if missing:
        errs.append(f"missing outlets on the dashboard: {missing}")

    zeros = [name for _, name in COLUMN_OUTLET
             if by.get(name, {}).get("total", 0) <= 0]
    if zeros:
        errs.append(f"outlets reporting zero sales: {zeros}")

    total = data.get("total_sales")
    if not total:
        errs.append("Total Sales missing from the summary cards")
    else:
        summed = sum(by.get(name, {}).get("total", 0) for _, name in COLUMN_OUTLET)
        if abs(summed - total) > 1.0:
            errs.append(
                f"outlet totals sum to {summed:,.2f} but Total Sales is "
                f"{total:,.2f} (diff {summed - total:,.2f})"
            )

    if not data.get("net_sales"):
        errs.append("Net Sales missing")
    if not data.get("total_orders"):
        errs.append("Total orders missing")
    if data.get("online_pct") is None:
        errs.append("Online % missing")
    if data.get("discount_pct") is None:
        errs.append("Discount % missing")

    z, s, online = data.get("zomato"), data.get("swiggy"), data.get("online_sales")
    if z is None or s is None:
        errs.append("Zomato/Swiggy split not readable (kebab tooltip)")
    elif online and abs((z + s) - online) > max(2.0, online * 0.01):
        errs.append(
            f"Zomato+Swiggy ({z + s:,.2f}) != Online Sales ({online:,.2f})"
        )
    return errs


# ---------------------------------------------------------------------------
# Row construction
# ---------------------------------------------------------------------------
def build_row(data: dict, row: int) -> list:
    """B..U for `row`. Index 11 is column M — deliberately blank (notes)."""
    by = data["by_outlet"]
    z, online = data["zomato"], data["online_sales"]
    zomato_pct = round((z / online) * 10000) / 100 if (z and online) else 0.0

    vals: list = [int(round(by[name]["total"])) for _, name in COLUMN_OUTLET]  # B..K
    vals.append(f"=SUM(B{row}:K{row})")                     # L
    vals.append("")                                          # M — notes, skipped
    vals.append(int(round(data["net_sales"])))               # N
    vals.append(f"=N{row}/L{row}")                           # O — percent-formatted after
    vals.append(f"{data['discount_pct']:.2f}%")              # P
    vals.append(f"{data['online_pct']:.2f}%")                # Q
    vals.append(int(data["total_orders"]))                   # R
    vals.append(f"=(L{row}*0.95)/R{row}")                    # S
    vals.append(f"{zomato_pct:.2f}%")                        # T
    vals.append(f"=100%-T{row}")                             # U — never hardcoded
    return vals


def _norm_daylabel(s: str):
    """('4th September' | '4th Sep' | '4 Sep') -> (4, 'sep'); None if unparseable.
    Column-A labels use the ABBREVIATED month ('4th Sep'); row_label() emits the
    full month ('4th September'), so we compare on (day, 3-letter month)."""
    import re
    m = re.match(r"\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,})", str(s))
    return (int(m.group(1)), m.group(2)[:3].lower()) if m else None


def find_target_row(grid: list[list[str]], label: str) -> int:
    """
    Return the 1-based sheet row whose column A matches `label` (day + month).

    Guard B: we match the label rather than appending after the last filled
    row, and we require B..U to be empty so a re-run can never double-write.
    """
    want = _norm_daylabel(label)
    for idx, r in enumerate(grid, start=1):
        if r and want is not None and _norm_daylabel(r[0]) == want:
            filled = [c for c in r[1:21] if (c or "").strip()]
            if filled:
                raise RuntimeError(
                    f"row {idx} ({label}) is already filled "
                    f"({len(filled)} non-empty cells in B..U) — refusing to overwrite. "
                    "Clear it first if this is a deliberate redo."
                )
            return idx
    seen = [r[0].strip() for r in grid if r and r[0].strip()]
    raise RuntimeError(
        f"no row in column A carries the label {label!r}. "
        "The tab may not have been extended for this month yet.\n"
        f"  column-A labels seen (last 20): {seen[-20:]}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="target date YYYY-MM-DD (default: yesterday)")
    ap.add_argument("--selftest", action="store_true",
                    help="scrape + gates only, write nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="scrape + locate row + preview the values, write nothing")
    ap.add_argument("--headed", action="store_true", help="visible browser")
    args = ap.parse_args()

    target = resolve_target(args.date)
    tab = WEEKDAY_TAB[target.weekday()]
    label = row_label(target)
    headless = not args.headed

    print(f"target      : {target.isoformat()} ({target.strftime('%A')})")
    print(f"tab / label : {tab} / {label}")

    # ---- pull -------------------------------------------------------------
    try:
        data = scrape_daily(target.isoformat(), headless=headless)
    except SessionExpired as e:
        print(f"\nSESSION EXPIRED: {e}")
        return 2

    def _fmt(v, spec=",.2f"):
        """Never let a missing value crash the report before the gates run."""
        try:
            return format(v, spec)
        except (TypeError, ValueError):
            return "MISSING"

    print(f"picker shows: {data['displayed_range']}")
    print(f"total sales : {_fmt(data['total_sales'])}")
    print(f"net sales   : {_fmt(data['net_sales'])}")
    print(f"orders      : {_fmt(data['total_orders'], ',')}")
    print(f"online      : {_fmt(data['online_sales'])} "
          f"(Z {data['zomato']} / S {data['swiggy']})")
    print(f"outlets read: {len(data['by_outlet'])}")

    errs = sanity(data)
    if errs:
        print("\nSANITY FAILED — nothing was written:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("sanity      : OK")

    if args.selftest:
        print("\nselftest only — no sheet access, nothing written.")
        return 0

    # ---- locate + write ---------------------------------------------------
    with BrowserWriter(headless=headless) as w:
        w.open_book(SALES_DATA_SHEET_ID)

        # Select the target weekday tab BEFORE any Name Box navigation. read_tab()
        # pulls data via gviz and never changes the visible tab, so without this
        # the workbook stays on whatever tab loaded by default. When that default
        # is a small tab (e.g. the ~27-row monthly summary), typing "A65" raises
        # Google's "Invalid range — exceeds the sheet size" and the Name Box snaps
        # back to A1 — which is the "reads 'A1'" write failure (fixed 2026-09-09).
        w.select_tab(tab)

        grid = w.read_tab(tab)
        gviz_row = find_target_row(grid, label)
        row = gviz_row
        print(f"target row  : {row} (from gviz index)")

        # Guard E (added 2026-09-07): the gviz CSV row index used by
        # find_target_row is not guaranteed to equal the true sheet row — a
        # misalignment once wrote a day's data one row above the target and
        # overwrote the previous day. Before writing, confirm on the LIVE sheet
        # (formula bar) that column A of `row` really carries this date's label;
        # if it's actually on an adjacent row, self-correct; otherwise abort.
        want = _norm_daylabel(label)
        if _norm_daylabel(w.read_selected_value(f"A{row}")) != want:
            corrected = None
            for cand in (row + 1, row - 1):
                if cand >= 1 and _norm_daylabel(w.read_selected_value(f"A{cand}")) == want:
                    corrected = cand
                    break
            if corrected is None:
                raise RuntimeError(
                    f"column A at row {row} is not {label!r} and neither adjacent "
                    "row matches — aborting so we never overwrite the wrong day.")
            print(f"row correction : {label!r} is actually at row {corrected}, not {row}")
            row = corrected

        values = build_row(data, row)
        preview = ", ".join(f"{col}={v}" for (col, _), v
                            in zip(COLUMN_OUTLET, values[:10]))
        print(f"outlets     : {preview}")
        print(f"L..U        : {values[10:]}")

        if args.dry_run:
            print("\ndry run — row located and values built, nothing written.")
            return 0

        w.select_tab(tab)
        w.write_rows_down(f"B{row}", [values])

        # Format fixes the sheet's convention expects.
        w.format_percent(f"O{row}")
        if row > 2:
            w.copy_format(f"S{row - 1}", f"S{row}")

        # ---- Guard D: read back through gviz ------------------------------
        # Read back in gviz-grid coordinates. Guard E moved `row` to the LIVE
        # sheet row for the Name-Box write, but read_tab() returns a gviz grid
        # whose index can be offset from the live row (the very misalignment
        # Guard E corrects). Use the ORIGINAL gviz index for grid access so we
        # read back the row we actually wrote, not an offset neighbour — this is
        # what caused the false "VERIFY FAILED / row missing on read-back" while
        # the data was in fact written correctly. (find_target_row can't be
        # reused here: post-write it would trip its "already filled" guard.)
        grid2 = w.read_tab(tab)
        if len(grid2) < gviz_row:
            print("VERIFY FAILED: row missing on read-back")
            return 1
        got = grid2[gviz_row - 1]

        problems = []
        for i, (col, name) in enumerate(COLUMN_OUTLET):
            want = int(round(data["by_outlet"][name]["total"]))
            have = (got[i + 1] if len(got) > i + 1 else "").replace(",", "").strip()
            try:
                ok = abs(float(have) - want) < 1
            except ValueError:
                ok = False
            if not ok:
                problems.append(f"{col}{row}: wrote {want}, read {have!r}")

        want_orders = int(data["total_orders"])
        have_orders = (got[17] if len(got) > 17 else "").replace(",", "").strip()
        try:
            if abs(float(have_orders) - want_orders) >= 1:
                problems.append(f"R{row}: wrote {want_orders}, read {have_orders!r}")
        except ValueError:
            problems.append(f"R{row}: orders unreadable ({have_orders!r})")

        if problems:
            print("\nVERIFY FAILED:")
            for p in problems:
                print(f"  - {p}")
            return 1

        print(f"\nOK — {tab}!{row} ({label}) written and verified.")
        print(f"   total {data['total_sales']:,.0f} · net {data['net_sales']:,.0f} "
              f"· orders {data['total_orders']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
