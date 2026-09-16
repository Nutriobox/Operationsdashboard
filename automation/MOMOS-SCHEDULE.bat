@echo off
REM Register the Momos Weekly update as a Windows scheduled task (Mon 06:15 IST).
REM Run ONCE, only after a clean headed validation (python momos_weekly.py --dry-run --headed)
REM AND after disabling the Claude "nutriobox-momos-dashboard--weekly-update-higgsfield" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_momos.bat
schtasks /create /tn "NutrioBox-Momos-Weekly" /sc weekly /d MON /st 06:15 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-Momos-Weekly" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
