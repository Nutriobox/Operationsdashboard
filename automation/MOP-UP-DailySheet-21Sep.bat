@echo off
REM One-shot retry for the only gap left in the 21-27 Sep backfill:
REM the Sales Data "Mon" tab, 21st September (missed on the flaky Name Box).
REM Safe: daily_sheet refuses to overwrite a row that is already filled.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
echo Retrying Daily Sheet for 2026-09-21 (Mon tab)...
call run_daily_sheet.bat --date 2026-09-21
echo.
powershell -NoProfile -Command "$l=(Select-String -Path logs\daily_sheet.log -Pattern '==== EXIT' | Select-Object -Last 1).Line; Write-Host ('daily_sheet last: ' + $l)"
pause
