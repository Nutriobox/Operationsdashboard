@echo off
REM Monthly re-sync of the closed month into DAILY_DATA. Port of nutriobox-monthly-resync (3rd).
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== MONTHLY RESYNC RUN %DATE% %TIME% ==== >> logs\monthly_resync.log
python refresh_tokens.py >> logs\monthly_resync.log 2>&1
python monthly_resync.py %* >> logs\monthly_resync.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\monthly_resync.log
