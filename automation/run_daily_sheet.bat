@echo off
REM Daily Dashboard fill - Playwright port of the Claude "petpooja-sales-to-gsheet" task.
REM Reads yesterday's per-outlet sales from the Petpooja dashboard JSON endpoints and
REM fills the day-of-week tab of the "Sales Data" sheet.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DAILY SHEET RUN %DATE% %TIME% ==== >> logs\daily_sheet.log
python refresh_tokens.py >> logs\daily_sheet.log 2>&1
REM 2026-09-29: switched from the browser (UI) writer to the DRIVE-API writer.
REM daily_sheet_drive.py pulls Petpooja over HTTP and updates the real .xlsx in
REM place via the Drive API using the service-account key — NO Google login, NO
REM copy-paste. The old browser writer (daily_sheet.py) is kept for reference.
python daily_sheet_drive.py %* >> logs\daily_sheet.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\daily_sheet.log
