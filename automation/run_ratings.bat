@echo off
REM Weekly ratings refresh: Zomato / Swiggy / Google -> Supabase, via Playwright.
REM Schedule this once a week (e.g. Mon 06:00) in Windows Task Scheduler.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
REM --headed: these sites (esp. Google) block headless Chromium as a bot. The
REM job runs a visible browser using the signed-in secrets\browser-profile.
echo ==== RATINGS RUN %DATE% %TIME% ==== >> logs\ratings.log
python ratings.py --headed >> logs\ratings.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\ratings.log
