@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
REM Shorten the sync-lag wait for validation (live schedule keeps the full 180s).
set NBDD_EXPORT_SLEEP=20
echo ==== DRY-RUN %DATE% %TIME% ==== > logs\dryrun.log
echo (writes nothing to the dashboard or Supabase) >> logs\dryrun.log
python daily_data.py --dry-run >> logs\dryrun.log 2>&1
echo DRYRUN_EXIT=%ERRORLEVEL% >> logs\dryrun.log
echo.
echo Dry-run finished. Full log: logs\dryrun.log
echo Showing the tail:
powershell -NoProfile -Command "Get-Content logs\dryrun.log -Tail 40"
echo.
pause
