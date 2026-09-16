@echo off
REM Read-only watchdog: scans logs\*.log for any job whose last run failed and
REM emails Satvik the exact fix. Reuses the Gmail creds in .env.local. Never
REM touches the pipeline. Scheduled by FAILURE-WATCH-SCHEDULE.bat.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== FAILURE WATCH RUN %DATE% %TIME% ==== >> logs\failure_watch.log
python failure_watch.py >> logs\failure_watch.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\failure_watch.log
