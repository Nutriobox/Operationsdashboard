@echo off
REM The actual scheduled job: refresh sessions, then run the sales pipeline.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== SCHEDULED RUN %DATE% %TIME% ==== >> logs\daily_data.log
python refresh_tokens.py >> logs\daily_data.log 2>&1
python daily_data.py >> logs\daily_data.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\daily_data.log
