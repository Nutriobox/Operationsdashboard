@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DELAY DRY-RUN %DATE% %TIME% ==== > logs\delay.log
echo (writes no files, publishes nothing) >> logs\delay.log
python delay_dashboard.py --dry-run --reader both >> logs\delay.log 2>&1
echo DRYRUN_EXIT=%ERRORLEVEL% >> logs\delay.log
echo.
powershell -NoProfile -Command "Get-Content logs\delay.log -Tail 40"
echo.
pause
