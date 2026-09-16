@echo off
REM Monthly item-wise dashboard rebuild. Port of nutriobox-monthly-dashboard (1st/2nd).
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== MONTHLY DASHBOARD RUN %DATE% %TIME% ==== >> logs\monthly_dashboard.log
python refresh_tokens.py >> logs\monthly_dashboard.log 2>&1
python monthly_dashboard.py %* >> logs\monthly_dashboard.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\monthly_dashboard.log
