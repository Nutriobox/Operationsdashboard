@echo off
REM One-click backfill of last week's Weekly KOT (Mon 24 Aug - Sun 30 Aug 2026)
REM via the native Playwright job. Refreshes the Petpooja session, pulls KOT +
REM Captain per outlet, creates and fills the "24th August - 30th August" tab in
REM the Weekly KOT sheet through the signed-in Google profile, and logs to
REM logs\kot_weekly.log. Safe to re-run: it refuses to duplicate an existing week.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
call run_kot_weekly.bat --monday 2026-08-24
echo.
echo ==== Backfill finished. Scroll up for the result, or open logs\kot_weekly.log ====
pause
