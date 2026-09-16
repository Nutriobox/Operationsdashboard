@echo off
REM One-time catch-up: fill last week's per-outlet sales into the Weekly 26 tab,
REM naming the tab explicitly (bypasses the --auto-tab detection that is failing).
REM The script's own guards will REFUSE to write if the column header/row doesn't
REM match the target week, so this cannot land data in the wrong place.
REM Double-click this file; the window stays open so you can read the result.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== WEEKLY SALES (manual --tab) RUN %DATE% %TIME% ==== >> logs\weekly_sales.log
python refresh_tokens.py >> logs\weekly_sales.log 2>&1
python weekly_sales_sync.py --tab "Weekly 26" > logs\_weekly_now.txt 2>&1
set RC=%ERRORLEVEL%
type logs\_weekly_now.txt
type logs\_weekly_now.txt >> logs\weekly_sales.log
echo ==== EXIT %RC% ==== >> logs\weekly_sales.log
echo.
echo ----------------------------------------------------------------
echo Done. Read the lines above: "Weekly tab: ..." + "wrote" = success.
echo An "ABORT:" line means it refused to write - copy that line to Claude.
echo ----------------------------------------------------------------
pause
