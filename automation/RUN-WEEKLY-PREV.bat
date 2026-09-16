@echo off
REM Catch-up for the PREVIOUS week (Aug 31 - Sep 6) into the Weekly 26 tab.
REM Uses --monday 2026-08-31 so it targets that week, and names the tab explicitly.
REM The script's guards refuse to write to the wrong column/row, so it is safe.
REM Double-click; the window stays open so you can read the result.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== WEEKLY SALES (manual prev-week) RUN %DATE% %TIME% ==== >> logs\weekly_sales.log
python refresh_tokens.py >> logs\weekly_sales.log 2>&1
python weekly_sales_sync.py --monday 2026-08-31 --tab "Weekly 26" > logs\_weekly_prev.txt 2>&1
set RC=%ERRORLEVEL%
type logs\_weekly_prev.txt
type logs\_weekly_prev.txt >> logs\weekly_sales.log
echo ==== EXIT %RC% ==== >> logs\weekly_sales.log
echo.
echo ----------------------------------------------------------------
echo Done. "Weekly tab: ..." + "wrote" = success.
echo An "ABORT:" line means it refused to write - copy that line to Claude.
echo ----------------------------------------------------------------
pause
