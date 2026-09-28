@echo off
REM ============================================================
REM  Repair September 2026 in the Sales Data sheet:
REM   [1] Full-fill the empty rows 19 + 20 + 21 Sep (robust whole-row write
REM       via daily_sheet; discount is correct now that dashboard_scrape is fixed).
REM   [2] resync_sep.py — fill any remaining empty boxes in other Sep dates and
REM       correct the Discount % (column P) to Petpooja's card value. Reads every
REM       write back to verify; never touches a cell that is already correct.
REM  Requires the Google login (DELAY-LOGIN.bat) — already done today.
REM  TIP: run AUDIT-SEP-dryrun.bat first to preview every change.
REM ============================================================
setlocal
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs

echo ==== [1] Full fill 19 + 20 + 21 Sep ====
for %%D in (2026-09-19 2026-09-20 2026-09-21) do (
  echo ---- daily_sheet %%D ----
  call run_daily_sheet.bat --date %%D
  echo ---- daily KOT   %%D ----
  call run_kot_daily.bat --date %%D
)

echo.
echo ==== [2] Fill remaining boxes + correct Discount %% for all September ====
echo ==== RESYNC SEP %DATE% %TIME% ==== >> logs\resync_sep.log
python refresh_tokens.py >> logs\resync_sep.log 2>&1
python resync_sep.py >> logs\resync_sep.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\resync_sep.log

echo.
echo ==== Done. Summary: ====
powershell -NoProfile -Command "Get-Content logs\resync_sep.log -Tail 20"
pause
