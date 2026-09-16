"""
kot-comparsion (WEEKLY) — ported from SKILL.md to plain Python.

  BEFORE:  a Claude browser run every Monday — outlet switching, in-page KOT
           submits, and ~40 Name-Box sheet writes, with the same tab-duplication
           and outlet-collision failure modes as the daily task.
  AFTER:   KOT via HTTP, Captain via one Playwright session, and the weekly tab
           created + filled through the Google Sheets UI with trusted input.
           Every write is read back through gviz and verified. No destination
           mirror — the weekly job writes only its own sheet. See
           KOT_WEEKLY_PORT.md.

Window (matches the SKILL exactly): the most recently completed Mon–Sun week,
both filters spanning [week-Monday 13:00:00 -> next-Monday 13:00:00).

Usage
  python kot_weekly.py --dry-run              pull + show what WOULD be written
  python kot_weekly.py --selftest             verify both readers (Petpooja + browser)
  python kot_weekly.py --headed               run with a visible browser (validation)
  python kot_weekly.py                        do it for real (last completed week)
  python kot_weekly.py --monday 2026-08-17    backfill a specific week (its Monday)
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
def target_monday(ref: date) -> date:
    """
    The Monday of the most recently COMPLETED Mon-Sun week, relative to `ref`.
    On a Monday this is ref-7; on any other day it's the Monday of the previous
    week. (this-week-Monday) - 7 days works for every weekday.
    """
    this_week_monday = ref - timedelta(days=ref.weekday())
    return this_week_monday - timedelta(days=7)


def _kot_fmt(d: date) -> str:
    """Petpooja's KOT date box: '15 Jun 2026 13:00:00' (no zero-padded day)."""
    return f"{d.day} {d.strftime('%b %Y')} 13:00:00"


def windows(mon: date):
    """Weekly window: [week-Monday 13:00 -> next-Monday 13:00)."""
    nxt = mon + timedelta(days=7)   # Sunday + 1 = next Monday
    return {
        "kot_from": _kot_fmt(mon),
        "kot_to":   _kot_fmt(nxt),
        "cap_from": mon.strftime("%Y-%m-%d 13:00:00"),
        "cap_to":   nxt.strftime("%Y-%m-%d 13:00:00"),
    }


def week_label(mon: date) -> str:
    """'15th June - 21st June' (each side keeps its own month across crossings)."""
    sun = mon + timedelta(days=6)
    return f"{kc.ordinal(mon.day)} {mon.strftime('%B')} - {kc.ordinal(sun.day)} {sun.strftime('%B')}"


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="pull and print, write nothing")
    ap.add_argument("--selftest", action="store_true", help="verify both readers are live")
    ap.add_argument("--monday", help="target week's Monday YYYY-MM-DD (default: last completed week)")
    ap.add_argument("--headed", action="store_true",
                    help="run the browser visibly (validation/debugging)")
    args = ap.parse_args()

    try:
        pp = Petpooja.from_tokens()
    except SessionExpired as e:
        print(f"ERROR: {e}")
        return 2

    if args.monday:
        mon = datetime.strptime(args.monday, "%Y-%m-%d").date()
        if mon.weekday() != 0:
            print(f"ERROR: --monday {args.monday} is a {mon.strftime('%A')}, not a Monday.")
            return 2
    else:
        mon = target_monday(datetime.now(kc.IST).date())

    w = windows(mon)
    label = week_label(mon)

    if args.selftest:
        return kc.liveness(pp, w["kot_from"], w["kot_to"],
                           w["cap_from"], w["cap_to"], headless=not args.headed)

    print(f"Target week: {label}  ({mon} .. {mon + timedelta(days=6)})")
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
        kc.write_source(results, config.KOT_WEEKLY_SHEET_ID, label, dry=True)
        print("\nDry run complete. Nothing was written.")
        return 0

    from sheet_writer import BrowserWriter, SessionExpired as SheetLogin, WriteError
    try:
        with BrowserWriter(headless=not args.headed) as writer:
            kc.write_source(results, config.KOT_WEEKLY_SHEET_ID, label,
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
