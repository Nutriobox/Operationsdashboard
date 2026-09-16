@echo off
REM The scheduled job: Wednesdays 06:00 IST. Appends last completed Mon-Sun week
REM to the delay dashboard (both local copies) and publishes to Supabase.
REM No Claude tokens - reads the sheet with Playwright, using the same persistent
REM profile refresh_tokens.py maintains. Falls back to nothing: if the Google
REM session is dead it aborts loudly rather than writing a partial week.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== SCHEDULED DELAY RUN %DATE% %TIME% ==== >> logs\delay.log
python delay_dashboard.py --reader playwright >> logs\delay.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\delay.log
