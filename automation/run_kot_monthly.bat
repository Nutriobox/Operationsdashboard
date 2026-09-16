@echo off
REM Monthly KOT comparison — Playwright port of the Claude "monthly-kot-comparison"
REM task. Pulls the calendar month that just ended: Total Dine In/Pickup KOT (HTTP)
REM and Captain App KOT (browser) per outlet, then creates + fills the "<Month>
REM <Year>" tab in the Monthly KOT sheet through the signed-in Google Sheets UI
REM (as mayank@). No destination mirror.
REM
REM Prereqs (already present on this laptop):
REM   - secrets\tokens.json kept fresh by refresh_tokens.py (Petpooja session)
REM   - secrets\browser-profile signed in to Google as mayank@nutriobox.com
REM     (same profile the daily/weekly KOT jobs use; if it logs out, run
REM      DELAY-LOGIN.bat once)
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== KOT MONTHLY RUN %DATE% %TIME% ==== >> logs\kot_monthly.log
python refresh_tokens.py >> logs\kot_monthly.log 2>&1
python kot_monthly.py %* >> logs\kot_monthly.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\kot_monthly.log
