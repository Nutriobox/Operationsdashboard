@echo off
REM Register the weekly Discount Analytics refresh as a Windows scheduled task
REM (Monday 06:00 IST). Run ONCE, only after a clean validation:
REM     python discount_weekly.py --dry-run
REM     python discount_weekly.py --headed      (watch the Petpooja pull once)
REM     python discount_weekly.py --publish     (one manual publish)
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_discount_weekly.bat
schtasks /create /tn "NutrioBox-DiscountWeekly" /sc weekly /d MON /st 06:00 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-DiscountWeekly" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
