@echo off
REM Daily Dashboard fill - Playwright port of the Claude "petpooja-sales-to-gsheet" task.
REM Reads yesterday's per-outlet sales from the Petpooja dashboard JSON endpoints and
REM fills the day-of-week tab of the "Sales Data" sheet.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DAILY SHEET RUN %DATE% %TIME% ==== >> logs\daily_sheet.log
REM 2026-09-30: REMOVED the "python refresh_tokens.py" pre-step. It launched a
REM headless Chromium against secrets/browser-profile, which HANGS/FAILS whenever
REM the profile is logged out (or the profile lock is held) — and that stall was
REM blocking the login-free writer below (see 30 Sep 10:45 run: header logged,
REM then nothing). daily_sheet_drive.py does NOT need a browser: it reads the
REM petpooja_cookie from secrets/tokens.json, which the 04:00 daily_data and 06:00
REM delay jobs already refresh every morning (well before this 10:45 run). If the
REM cookie is ever stale, daily_sheet_drive.py exits non-zero and failure_watch
REM alerts — it will not silently hang.
REM 2026-09-29: switched from the browser (UI) writer to the DRIVE-API writer.
REM daily_sheet_drive.py pulls Petpooja over HTTP and updates the real .xlsx in
REM place via the Drive API using the service-account key — NO Google login, NO
REM copy-paste. The old browser writer (daily_sheet.py) is kept for reference.
REM 2026-10-21: run through daily_sheet_backfill.py instead of calling the writer
REM directly. It fills ANY still-empty row in the last 5 days (not just yesterday),
REM so a run missed because the 10:45 trigger didn't fire (laptop off/asleep) is
REM recovered automatically on the next run that DOES fire. Each day is still the
REM proven daily_sheet_drive.py writer, which refuses to overwrite filled rows, so
REM this is safe + idempotent. A manual single day still works:  run_daily_sheet.bat --date YYYY-MM-DD
python daily_sheet_backfill.py 5 %* >> logs\daily_sheet.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\daily_sheet.log
