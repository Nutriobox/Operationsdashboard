@echo off
cd /d "%~dp0"
echo ============================================================
echo   NutrioBox Vehicle Report - one-time installer
echo ============================================================
echo.
echo [1/2] Installing Python packages (requests, openpyxl)...
python -m pip install --user requests openpyxl
if errorlevel 1 (
  echo.
  echo Could not run "python". Install Python 3 from python.org
  echo ^(tick "Add Python to PATH" during install^), then run this again.
  pause
  exit /b 1
)
echo.
echo [2/2] Creating the daily 8:00 PM scheduled task...
schtasks /create /tn "NutrioBox Vehicle Report" /tr "\"%~dp0RUN-vehicle-report.bat\"" /sc daily /st 20:00 /f
echo.
echo ============================================================
echo   DONE.
echo   Next: open  vehicle_report_config.py  in Notepad, type your
echo   OneLap + Gmail details in the 4 lines marked ^<^<^<, save it,
echo   then double-click RUN-vehicle-report.bat to test.
echo ============================================================
pause
