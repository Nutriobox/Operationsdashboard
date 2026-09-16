@echo off
REM Register the Daily Dashboard fill as a Windows scheduled task (daily 10:45 IST).
REM 10:45 keeps it clear of the 04:00 daily-data pull. Run ONCE, only after a clean
REM headed validation (python daily_sheet.py --dry-run --headed) AND after disabling
REM the Claude "petpooja-sales-to-gsheet" task.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set JOB=C:\Users\hp\Downloads\Operationsdashboard\automation\run_daily_sheet.bat
schtasks /create /tn "NutrioBox-DailySheet" /sc daily /st 10:45 /f /tr "%JOB%"
schtasks /query /tn "NutrioBox-DailySheet" /fo LIST | findstr /i "TaskName Next Status"
echo.
pause
