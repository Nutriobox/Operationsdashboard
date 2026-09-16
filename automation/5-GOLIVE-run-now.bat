@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
REM One-time LIVE run: updates the local dashboard HTML and publishes to Supabase.
set NBDD_EXPORT_SLEEP=20
echo ==== GO-LIVE RUN %DATE% %TIME% ==== > logs\golive.log
python daily_data.py >> logs\golive.log 2>&1
echo GOLIVE_EXIT=%ERRORLEVEL% >> logs\golive.log
echo.
echo Finished. Tail of the log:
powershell -NoProfile -Command "Get-Content logs\golive.log -Tail 30"
echo.
pause
