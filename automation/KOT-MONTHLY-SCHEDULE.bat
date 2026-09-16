@echo off
REM Register the monthly KOT comparison as a Windows scheduled task.
REM Runs on the 1st of every month at 12:30 IST — clear of the ~10:30
REM petpooja-sales-to-gsheet and the ~11:15 nutriobox-monthly-dashboard runs
REM (avoids the shared-Petpooja "outlet-session collision"; kot_monthly
REM re-switches + retries anyway).
REM
REM Run this ONCE, only after a clean headed validation:
REM     python kot_monthly.py --headed --month <YYYY-MM of last month>
REM and only after you've disabled the old Claude "monthly-kot-comparison" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_kot_monthly.bat
echo ==== KOT MONTHLY SCHEDULE %DATE% %TIME% ==== > logs\kot_monthly_schedule.log
schtasks /create /tn "NutrioBox-KOT-Monthly" /sc monthly /d 1 /st 12:30 /f /tr "%JOB%" >> logs\kot_monthly_schedule.log 2>&1
echo --- verify --- >> logs\kot_monthly_schedule.log
schtasks /query /tn "NutrioBox-KOT-Monthly" /fo LIST ^| findstr /i "TaskName Next Status" >> logs\kot_monthly_schedule.log 2>&1
echo KOT_MONTHLY_SCHEDULE_DONE >> logs\kot_monthly_schedule.log
type logs\kot_monthly_schedule.log
echo.
pause
