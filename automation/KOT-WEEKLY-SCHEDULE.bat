@echo off
REM Register the weekly KOT comparison as a Windows scheduled task.
REM Runs Monday 11:20 IST — after the 04:00 daily-data AM pull and the ~10:55
REM petpooja-weekly-sales-sync have finished (avoids the shared-Petpooja
REM "outlet-session collision"; kot_weekly re-switches + retries anyway).
REM
REM Run this ONCE, only after a clean headed validation:
REM     python kot_weekly.py --headed --monday <last-week-Monday>
REM and only after you've disabled the old Claude "kot-comparsion" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_kot_weekly.bat
echo ==== KOT WEEKLY SCHEDULE %DATE% %TIME% ==== > logs\kot_weekly_schedule.log
schtasks /create /tn "NutrioBox-KOT-Weekly" /sc weekly /d MON /st 11:20 /f /tr "%JOB%" >> logs\kot_weekly_schedule.log 2>&1
echo --- verify --- >> logs\kot_weekly_schedule.log
schtasks /query /tn "NutrioBox-KOT-Weekly" /fo LIST ^| findstr /i "TaskName Next Status" >> logs\kot_weekly_schedule.log 2>&1
echo KOT_WEEKLY_SCHEDULE_DONE >> logs\kot_weekly_schedule.log
type logs\kot_weekly_schedule.log
echo.
pause
