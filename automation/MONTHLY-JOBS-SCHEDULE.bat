@echo off
REM Register the three monthly jobs. Run ONCE, after validating each with --dry-run
REM (and finishing their VALIDATE export/reconcile stubs). Then DISABLE the Claude
REM twins: nutriobox-monthly-dashboard, nutriobox-monthly-resync,
REM nutriobox-dashboard-monday-reminder.
setlocal
set A=C:\Users\hp\Downloads\Operationsdashboard\automation
schtasks /create /tn "NutrioBox-MonthlyDashboard" /sc monthly /d 1   /st 11:15 /f /tr "%A%\run_monthly_dashboard.bat" >nul
schtasks /create /tn "NutrioBox-MonthlyResync"    /sc monthly /d 3   /st 05:30 /f /tr "%A%\run_monthly_resync.bat"    >nul
schtasks /create /tn "NutrioBox-MonthlyReminder"  /sc monthly /d 1   /st 11:30 /f /tr "%A%\run_monday_reminder.bat"   >nul
for %%T in (NutrioBox-MonthlyDashboard NutrioBox-MonthlyResync NutrioBox-MonthlyReminder) do (
  schtasks /query /tn "%%T" /fo LIST 2>&1 | findstr /i "TaskName Next Status"
)
echo.
pause
