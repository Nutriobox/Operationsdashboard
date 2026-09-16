@echo off
REM One-shot: register the 5 validated Playwright jobs as Windows scheduled tasks.
REM Only registers (schtasks /create) — does NOT run any job. Results go to
REM logs\register_all.log so they can be verified programmatically.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set A=C:\Users\hp\Downloads\Operationsdashboard\automation
set LOG=logs\register_all.log
echo ==== REGISTER ALL %DATE% %TIME% ==== > "%LOG%"
schtasks /create /tn "NutrioBox-KOT-Monthly"      /sc monthly /d 1  /st 12:30 /f /tr "%A%\run_kot_monthly.bat"        >> "%LOG%" 2>&1
schtasks /create /tn "NutrioBox-WeeklySales"      /sc weekly  /d MON /st 12:15 /f /tr "%A%\run_weekly_sales.bat"       >> "%LOG%" 2>&1
schtasks /create /tn "NutrioBox-Momos-Weekly"     /sc weekly  /d MON /st 06:15 /f /tr "%A%\run_momos.bat"              >> "%LOG%" 2>&1
schtasks /create /tn "NutrioBox-MonthlySalesFill" /sc weekly  /d MON /st 07:00 /f /tr "%A%\run_monthly_sales_fill.bat" >> "%LOG%" 2>&1
schtasks /create /tn "NutrioBox-DailySheet"       /sc daily        /st 10:45 /f /tr "%A%\run_daily_sheet.bat"         >> "%LOG%" 2>&1
echo ---- QUERY ---- >> "%LOG%"
for %%T in (NutrioBox-KOT-Monthly NutrioBox-WeeklySales NutrioBox-Momos-Weekly NutrioBox-MonthlySalesFill NutrioBox-DailySheet) do (
  schtasks /query /tn "%%T" /fo LIST 2>&1 | findstr /i "TaskName Next Status" >> "%LOG%"
)
echo ==== DONE ==== >> "%LOG%"
