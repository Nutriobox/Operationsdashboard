@echo off
REM Re-runs everything that failed 20-23 Sep 2026 while the Google login was dead.
REM Sheets are now written by the robot account, so no Google login is needed.
REM Each job refuses to overwrite a row that's already filled, so this is safe.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
echo [1/8] Daily KOT 21 Sep
call run_kot_daily.bat --date 2026-09-21
echo [2/8] Daily KOT 22 Sep
call run_kot_daily.bat --date 2026-09-22
echo [3/8] Daily Sheet 20 Sep
call run_daily_sheet.bat --date 2026-09-20
echo [4/8] Daily Sheet 21 Sep
call run_daily_sheet.bat --date 2026-09-21
echo [5/8] Daily Sheet 22 Sep
call run_daily_sheet.bat --date 2026-09-22
echo [6/8] Delay dashboard (last week)
call run_delay.bat
echo [7/8] Incentive delay (last week)
call run_incentive_delay.bat
echo [8/8] Monthly sales fill (month to date)
call run_monthly_sales_fill.bat
echo.
echo ==== Finished. Latest result of each job: ====
for %%L in (kot_daily daily_sheet delay incentive_delay monthly_sales_fill) do (
  powershell -NoProfile -Command "$l=(Select-String -Path logs\%%L.log -Pattern '==== EXIT' | Select-Object -Last 1).Line; Write-Host ('%%L'.PadRight(20) + $l)"
)
pause
