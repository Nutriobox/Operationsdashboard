@echo off
REM ============================================================
REM  Backfill the Sales Data sheet for the week 21-27 Sep 2026
REM  (Mon..Sun day tabs) + the Daily KOT for the same week.
REM
REM  PREREQUISITE: the Sales Data sheet is an uploaded .xlsx, so it is
REM  written by the SIGNED-IN Chrome (UI) writer, NOT the robot API.
REM  You MUST run  DELAY-LOGIN.bat  and sign in as mayank@nutriobox.com
REM  FIRST, or every daily_sheet step will fail with SessionExpired.
REM
REM  Safe to re-run: each job refuses to overwrite a row that is
REM  already filled, so completed days are skipped.
REM ============================================================
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs

for %%D in (2026-09-21 2026-09-22 2026-09-23 2026-09-24 2026-09-25 2026-09-26 2026-09-27) do (
  echo ==== Daily Sheet %%D ====
  call run_daily_sheet.bat --date %%D
  echo ==== Daily KOT   %%D ====
  call run_kot_daily.bat --date %%D
)

echo.
echo ==== Finished. Latest EXIT of each job: ====
for %%L in (daily_sheet kot_daily) do (
  powershell -NoProfile -Command "$l=(Select-String -Path logs\%%L.log -Pattern '==== EXIT' | Select-Object -Last 1).Line; Write-Host ('%%L'.PadRight(14) + $l)"
)
pause
