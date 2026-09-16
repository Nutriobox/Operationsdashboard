@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DELAY SELFTEST %DATE% %TIME% ==== > logs\delay.log
echo (Playwright reader, cross-checked against the Sheets API - writes nothing) >> logs\delay.log
python delay_dashboard.py --selftest --reader both >> logs\delay.log 2>&1
echo SELFTEST_EXIT=%ERRORLEVEL% >> logs\delay.log
echo.
powershell -NoProfile -Command "Get-Content logs\delay.log -Tail 40"
echo.
echo (full log: %CD%\logs\delay.log)
echo.
pause
