@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set "LOG=logs\delay-status.log"

echo ================================================== >> "%LOG%"
echo ==== DELAY STATUS %DATE% %TIME% ==== >> "%LOG%"
echo ================================================== >> "%LOG%"

echo.
echo [1/3] Is the weekly schedule registered?
echo --- schedule --- >> "%LOG%"
schtasks /query /tn "NutrioBox-Delay-Weekly" /fo list >> "%LOG%" 2>&1
if errorlevel 1 (
  echo    NOT REGISTERED - run DELAY-3-GOLIVE.bat
  echo NOT REGISTERED >> "%LOG%"
) else (
  echo    registered
)

echo.
echo [2/3] Self-test - Playwright, cross-checked against the Sheets API...
echo. >> "%LOG%"
echo --- selftest --reader both --- >> "%LOG%"
python delay_dashboard.py --selftest --reader both >> "%LOG%" 2>&1
echo SELFTEST_EXIT=%ERRORLEVEL% >> "%LOG%"
if errorlevel 1 (echo    FAILED - see the log) else (echo    passed)

echo.
echo [3/3] Dry run - full read path, writes nothing...
echo. >> "%LOG%"
echo --- dry run --reader both --- >> "%LOG%"
python delay_dashboard.py --dry-run --reader both >> "%LOG%" 2>&1
echo DRYRUN_EXIT=%ERRORLEVEL% >> "%LOG%"
if errorlevel 1 (echo    FAILED - see the log) else (echo    passed)

echo.
echo ---------------------------------------------------
powershell -NoProfile -Command "Get-Content '%LOG%' -Tail 55"
echo ---------------------------------------------------
echo.
echo Full history: %CD%\%LOG%
echo.
pause
