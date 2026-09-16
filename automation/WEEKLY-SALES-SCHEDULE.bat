@echo off
REM Register the weekly sales sync as a Windows scheduled task (Mon 12:15 IST).
REM Run ONCE, only after a clean headed validation:
REM     python weekly_sales_sync.py --dry-run
REM     python weekly_sales_sync.py --headed --auto-tab
REM and only after disabling the Claude "petpooja-weekly-sales-sync" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_weekly_sales.bat
schtasks /create /tn "NutrioBox-WeeklySales" /sc weekly /d MON /st 12:15 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-WeeklySales" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
