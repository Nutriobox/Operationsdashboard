@echo off
REM Catch-up for the daily jobs that write the .xlsx and were missed/failed because
REM the Google login dropped overnight (laptop off -> keepalive couldn't run).
REM daily_data (sales dashboard) already ran at 04:00, so it's NOT repeated here.
REM
REM PREREQUISITE: run DELAY-LOGIN.bat FIRST and sign in as mayank@nutriobox.com,
REM then close that window. Otherwise both steps fail with SessionExpired.
REM
REM Both jobs default to YESTERDAY's date and refuse to overwrite a filled row,
REM so this is safe and re-runnable.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs

echo ==== [1/2] Daily KOT (yesterday) ====
call run_kot_daily.bat
echo ==== [2/2] Daily Sheet -> main .xlsx (yesterday) ====
call run_daily_sheet.bat

echo.
echo ==== Results (latest EXIT of each) ====
for %%L in (kot_daily daily_sheet) do (
  powershell -NoProfile -Command "$l=(Select-String -Path logs\%%L.log -Pattern '==== EXIT' | Select-Object -Last 1).Line; Write-Host ('%%L'.PadRight(14) + $l)"
)
pause
