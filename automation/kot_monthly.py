"""
monthly-kot-comparison (MONTHLY) — ported from SKILL.md to plain Python.

  BEFORE:  a Claude browser run on the 1st of each month — same outlet switching,
           in-page KOT submits, and Name-Box sheet writes as the weekly task,
           with the same collision/duplication failure modes.
  AFTER:   KOT via HTTP, Captain via one Playwright session, and the month tab
           created/filled through the Google Sheets UI with trusted input. Every
           write is read back through gviz and verified. No destination mirror —
           the monthly job writes only its own "Monthly KOT" sheet. See
           KOT_MONTHLY_PORT.md.

Window (matches the SKILL exactly): the calendar month that just ended, both
filters spanning [1st of that month 00:00:00 -> 1st of next month 00:00:00).
Tab name is the month's full name + year, e.g. "July 2026".

Usage
  python kot_monthly.py --dry-run           pull + show what WOULD be written
  python kot_monthly.py --selftest          verify both readers (Petpooja + browser)
  python kot_monthly.py --headed            run with a visible browser (validation)
  python kot_monthly.py                     do it for real (previous calendar month)
  python kot_monthly.py --month 2026-07     backfill a specific month (YYYY-MM)
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, date, timedelta

import config
import kot_common as kc
from petpooja import Petpooja, SessionExpired, ScrapeError


# ---------------------------------------------------------------------------
# dates
# ---------------------------------------------------------------------------
def first_of_next_month(first: date) -> date:
    if first.month == 12:
        return date(first.year + 1, 1, 1)
    return date(first.year, first.month + 1, 1)


def previous_month_first(ref: date) -> date:
    """First day of the calendar month that just ended, relative to `ref`."""
    this_month_first = ref.replace(day=1)
    last_day_prev = this_month_first - timedelta(days=1)
    return last_day_prev.replace(day=1)


def _kot_fmt(d: date) -> str:
    """Petpooja's KOT date box: '1 Jul 2026 00:00:00' (no zero-padded day)."""
    return f"{d.day} {d.strftime('%b %Y')} 00:00:00"


def windows(first: date):
    """Monthly window: [1st of month 00:00 -> 1st of next month 00:00)."""
    nxt = first_of_next_month(first)
    return {
        "kot_from": _kot_fmt(first),
        "kot_to":   _kot_fmt(nxt),
        "cap_from": first.strftime("%Y-%m-%d 00:00:00"),
        "cap_to":   nxt.strftime("%Y-%m-%d 00:00:00"),
    }


def month_label(first: date) -> str:
    """'July 2026'."""
    return first.strftime("%B %Y")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="pull and print, write nothing")
    ap.add_argument("--selftest", action="store_true", help="verify both readers are live")
    ap.add_argument("--month", help="target month YYYY-MM (default: previous calendar month)")
    ap.add_argument("--headed", action="store_true",
                    help="run the browser visibly (validation/debugging)")
    args = ap.parse_args()

    try:
        pp = Petpooja.from_tokens()
    except SessionExpired as e:
        print(f"ERROR: {e}")
        return 2

    if args.month:
        try:
            first = datetime.strptime(args.month, "%Y-%m").date().replace(day=1)
        except ValueError:
            print(f"ERROR: --month {args.month!r} must be YYYY-MM (e.g. 2026-07).")
            return 2
    else:
        first = previous_month_first(datetime.now(kc.IST).date())

    w = windows(first)
    label = month_label(first)

    if args.selftest:
        return kc.liveness(pp, w["kot_from"], w["kot_to"],
                           w["cap_from"], w["cap_to"], headless=not args.headed)

    print(f"Target month: {label}  ({first} .. {first_of_next_month(first)})")
    print(f"Mode: {'DRY RUN — nothing will be written' if args.dry_run else 'LIVE'}\n")

    try:
        results = kc.pull(pp, w["kot_from"], w["kot_to"],
                          w["cap_from"], w["cap_to"], headless=not args.headed)
    except (SessionExpired, ScrapeError) as e:
        print(f"\nERROR during Petpooja pull: {e}")
        return 2

    problems = kc.sanity(results)
    if problems:
        print("\nSANITY CHECK FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 2

    kc.print_totals(results)

    if args.dry_run:
        kc.write_source(results, config.KOT_MONTHLY_SHEET_ID, label, dry=True)
        print("\nDry run complete. Nothing was written.")
        return 0

    from sheet_writer import BrowserWriter, SessionExpired as SheetLogin, WriteError
    try:
        with BrowserWriter(headless=not args.headed) as writer:
            kc.write_source(results, config.KOT_MONTHLY_SHEET_ID, label,
                            dry=False, writer=writer, write_a1=False)
    except (ScrapeError, WriteError) as e:
        print(f"\nERROR: {e}")
        return 2
    except SheetLogin as e:
        print(f"\nERROR (Google session): {e}")
        return 2

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
