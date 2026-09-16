@echo off
REM Incentive - MONTHLY metrics (rows 3,15,18). Port of incentive--monthly-metrics-1st-of-month.
REM Run AFTER monthly_sales_fill + monthly dashboard have filled the Sales Data tabs.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== INCENTIVE MONTHLY RUN %DATE% %TIME% ==== >> logs\incentive_monthly.log
python refresh_tokens.py >> logs\incentive_monthly.log 2>&1
python incentive_monthly.py %* >> logs\incentive_monthly.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\incentive_monthly.log
