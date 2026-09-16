@echo off
setlocal
REM Registers the WEEKLY ratings refresh in Windows Task Scheduler.
REM Runs run_ratings.bat every Monday at 06:00. Re-running is safe (/f overwrites).
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_ratings.bat
echo ==== SCHEDULE RATINGS %DATE% %TIME% ==== > logs\schedule-ratings.log
schtasks /create /tn "NutrioBox-Ratings-Weekly" /sc weekly /d MON /st 06:00 /f /tr "%JOB%" >> logs\schedule-ratings.log 2>&1
echo --- verify --- >> logs\schedule-ratings.log
schtasks /query /tn "NutrioBox-Ratings-Weekly" /fo LIST >> logs\schedule-ratings.log 2>&1
echo SCHEDULE_DONE >> logs\schedule-ratings.log
type logs\schedule-ratings.log
echo.
pause
