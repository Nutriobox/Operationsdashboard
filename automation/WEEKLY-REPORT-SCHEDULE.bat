@echo off
REM Register the weekly consolidated report as a Windows scheduled task
REM (Wednesday 03:00 IST). Run ONCE, and ONLY after a clean validation:
REM     python weekly_report.py --selftest                          (all 5 sources pull, no write)
REM     python weekly_report.py --headed --dry-run --monday <last-Monday>
REM     python weekly_report.py --headed --monday <last-Monday>     (one watched manual run)
REM Confirm the written numbers match a known-good week BEFORE scheduling.
REM Then DISABLE the Claude twin "weekly-petpooja-sales-report" in the SAME pass
REM (or both race the Petpooja outlet session - the July-corruption bug).
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_weekly_report.bat
schtasks /create /tn "NutrioBox-WeeklyReport" /sc weekly /d WED /st 03:00 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-WeeklyReport" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
