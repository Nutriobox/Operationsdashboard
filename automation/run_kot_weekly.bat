@echo off
REM Weekly KOT comparison — Playwright port of the Claude "kot-comparsion" task.
REM Pulls the last completed Mon-Sun week's Total Dine In/Pickup KOT (HTTP) and
REM Captain App KOT (browser) per outlet, then creates + fills the week tab in the
REM Weekly KOT sheet through the signed-in Google Sheets UI (as mayank@). No
REM destination mirror.
REM
REM Prereqs (already present on this laptop):
REM   - secrets\tokens.json kept fresh by refresh_tokens.py (Petpooja session)
REM   - secrets\browser-profile signed in to Google as mayank@nutriobox.com
REM     (same profile the daily KOT / ratings / delay jobs use; if it logs out,
REM      run DELAY-LOGIN.bat once)
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== KOT WEEKLY RUN %DATE% %TIME% ==== >> logs\kot_weekly.log
python refresh_tokens.py >> logs\kot_weekly.log 2>&1
python kot_weekly.py %* >> logs\kot_weekly.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\kot_weekly.log
