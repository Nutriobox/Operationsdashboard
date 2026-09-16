@echo off
REM Register the failure watchdog to run every 4 hours (08:00, 12:00, 16:00, 20:00,
REM 00:00, 04:00). De-dup in failure_watch.py means you get one email per NEW
REM incident, not one every 4 hours. Run ONCE. Then run HARDEN-SCHEDULED-TASKS.bat
REM so this task also catches up if the laptop was off at a check time.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_failure_watch.bat
schtasks /create /tn "NutrioBox-FailureWatch" /sc hourly /mo 4 /st 08:00 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-FailureWatch" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
