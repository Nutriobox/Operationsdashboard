@echo off
REM Daily Dashboard fill - Playwright port of the Claude "petpooja-sales-to-gsheet" task.
REM Reads yesterday's per-outlet sales from the Petpooja dashboard JSON endpoints and
REM fills the day-of-week tab of the "Sales Data" sheet.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DAILY SHEET RUN %DATE% %TIME% ==== >> logs\daily_sheet.log
python refresh_tokens.py >> logs\daily_sheet.log 2>&1
python daily_sheet.py %* >> logs\daily_sheet.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\daily_sheet.log
