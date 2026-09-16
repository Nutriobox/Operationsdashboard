@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs

echo Running self-test (writes nothing)...
echo ==== SELFTEST %DATE% %TIME% ==== > logs\selftest.log
python daily_data.py --selftest >> logs\selftest.log 2>&1
echo SELFTEST_EXIT=%ERRORLEVEL% >> logs\selftest.log
type logs\selftest.log

echo.
echo ============================================================
echo Self-test done. Log: logs\selftest.log
echo If it says "Client is healthy", the dry-run below is safe.
echo ============================================================
pause
