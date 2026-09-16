@echo off
REM Daily KOT comparison — Playwright port of the Claude "daily-kot-comparison"
REM task. Pulls yesterday's Total Dine In/Pickup KOT (HTTP) and Captain App KOT
REM (browser) per outlet, then writes the SOURCE Google Sheet and the DESTINATION
REM "Sales Data" xlsx through the signed-in Google Sheets UI (as mayank@).
REM
REM Prereqs (already present on this laptop):
REM   - secrets\tokens.json kept fresh by refresh_tokens.py (Petpooja session)
REM   - secrets\browser-profile signed in to Google as mayank@nutriobox.com
REM     (the same profile ratings.py / delay_dashboard.py use; if it logs out,
REM      run DELAY-LOGIN.bat once)
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== KOT DAILY RUN %DATE% %TIME% ==== >> logs\kot_daily.log
python refresh_tokens.py >> logs\kot_daily.log 2>&1
python kot_daily.py %* >> logs\kot_daily.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\kot_daily.log
