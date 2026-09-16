@echo off
REM Incentive - WEEKLY metrics (rows 6,9,12,21,24). Port of incentive--weekly-metrics-first-monday.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== INCENTIVE WEEKLY RUN %DATE% %TIME% ==== >> logs\incentive_weekly.log
python refresh_tokens.py >> logs\incentive_weekly.log 2>&1
python incentive_weekly.py %* >> logs\incentive_weekly.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\incentive_weekly.log
