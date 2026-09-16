@echo off
REM Register the Monthly Sales Fill as a Windows scheduled task (Mon 07:00 IST).
REM 07:00 is clear of the 06:15 Momos and the 06:00 discount/ratings jobs. Run ONCE,
REM only after a clean headed validation (python monthly_sales_fill.py --dry-run --headed)
REM AND after disabling the Claude "nutriobox-weekly-petpooja-sales-fill" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_monthly_sales_fill.bat
schtasks /create /tn "NutrioBox-MonthlySalesFill" /sc weekly /d MON /st 07:00 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-MonthlySalesFill" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
