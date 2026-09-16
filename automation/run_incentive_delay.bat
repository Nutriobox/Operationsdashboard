@echo off
REM Incentive - weekly DELAY metrics (rows 9,12). Port of incentive-delay-metrics-weekly-wed.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== INCENTIVE DELAY RUN %DATE% %TIME% ==== >> logs\incentive_delay.log
python refresh_tokens.py >> logs\incentive_delay.log 2>&1
python incentive_delay.py %* >> logs\incentive_delay.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\incentive_delay.log
