@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_daily.bat
echo ==== SCHEDULE %DATE% %TIME% ==== > logs\schedule.log
schtasks /create /tn "NutrioBox-DailyData-AM" /sc daily /st 04:00 /f /tr "%JOB%" >> logs\schedule.log 2>&1
schtasks /create /tn "NutrioBox-DailyData-PM" /sc daily /st 16:00 /f /tr "%JOB%" >> logs\schedule.log 2>&1
echo --- verify --- >> logs\schedule.log
schtasks /query /tn "NutrioBox-DailyData-AM" /fo LIST ^| findstr /i "TaskName Next Status" >> logs\schedule.log 2>&1
schtasks /query /tn "NutrioBox-DailyData-PM" /fo LIST ^| findstr /i "TaskName Next Status" >> logs\schedule.log 2>&1
echo SCHEDULE_DONE >> logs\schedule.log
type logs\schedule.log
echo.
pause
