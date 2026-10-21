#!/usr/bin/env python3
"""
daily_sheet_backfill.py  —  self-healing wrapper around daily_sheet_drive.py
(added 2026-10-21 by Satvik's ops assistant)

WHY THIS EXISTS
---------------
The Windows task "NutrioBox-DailySheet" fires once a day at 10:45 and the writer
(daily_sheet_drive.py) fills ONLY yesterday's row. If that single 10:45 trigger
is ever missed — e.g. the laptop was off/asleep at 10:45 and the task had no
"run when missed" catch-up — the day is silently lost forever, because the next
run only looks at the *new* yesterday. That is exactly what happened on
21 Oct 2026 (the 20 Oct row stayed blank).

WHAT IT DOES
------------
Default (no --date): walk the last N days (N = first bare integer arg, default 5)
and run the proven writer for each. daily_sheet_drive.py already PULLS fresh
Petpooja data, refuses to overwrite a filled row, and exits 0 for an
already-filled day — so this is safe + idempotent. Any day whose row is still
empty (because its own 10:45 run was missed) gets back-filled automatically on
the next run that DOES fire. No manual catch-up needed.

If --date YYYY-MM-DD is passed, it forwards to daily_sheet_drive.py for that one
day only (single-day manual behaviour preserved).

EXIT CODE
---------
Governed by YESTERDAY only (i == 1): 0 if yesterday was written or already
present, else yesterday's non-zero code — so failure_watch still alerts on a
real same-day failure (e.g. a stale Petpooja cookie). Older days (i >= 2) are
best-effort recovery and never fail the run, so an un-fillable old gap can't spam
alerts.
"""
import subprocess
import sys
import datetime
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DRIVER = HERE / "daily_sheet_drive.py"


def main():
    argv = sys.argv[1:]
    n = None
    rest = []
    for a in argv:
        if n is None and a.isdigit():
            n = int(a)
        else:
            rest.append(a)
    if n is None:
        n = 5

    # Explicit single-day request -> straight passthrough.
    if "--date" in rest:
        return subprocess.run([sys.executable, str(DRIVER)] + rest).returncode

    today = datetime.date.today()
    exit_code = 0
    for i in range(1, n + 1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        print(f"\n----- backfill check: {d} (day -{i}) -----", flush=True)
        rc = subprocess.run(
            [sys.executable, str(DRIVER), "--date", d] + rest
        ).returncode
        if i == 1:
            # Yesterday governs the run's health / alerting.
            exit_code = rc
        else:
            print(f"      (day -{i} best-effort recovery, rc={rc})", flush=True)

    print(f"\n===== backfill window={n}d complete, exit={exit_code} =====",
          flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
