@echo off
REM Register the daily KOT comparison as a Windows scheduled task.
REM Runs 05:15 IST — after the 04:00 daily-data AM Petpooja pull has finished and
REM yesterday's business day (01:00->01:00) has fully closed.
REM
REM Run this ONCE, only after a clean headed validation:
REM     python kot_daily.py --headed --date <yesterday>
REM and only after you've disabled the old Claude "daily-kot-comparison" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_kot_daily.bat
echo ==== KOT SCHEDULE %DATE% %TIME% ==== > logs\kot_schedule.log
schtasks /create /tn "NutrioBox-KOT-Daily" /sc daily /st 05:15 /f /tr "%JOB%" >> logs\kot_schedule.log 2>&1
echo --- verify --- >> logs\kot_schedule.log
schtasks /query /tn "NutrioBox-KOT-Daily" /fo LIST ^| findstr /i "TaskName Next Status" >> logs\kot_schedule.log 2>&1
echo KOT_SCHEDULE_DONE >> logs\kot_schedule.log
type logs\kot_schedule.log
echo.
pause
