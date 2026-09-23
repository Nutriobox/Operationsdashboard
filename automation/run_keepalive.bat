@echo off
REM Keep-alive: visits Petpooja/Zomato/Swiggy headlessly so their sessions never
REM sit idle long enough to expire (Petpooja expires 24h after last use).
REM Scheduled every 4 hours by KEEPALIVE-SCHEDULE.bat (added 2026-09-23).
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== KEEPALIVE RUN %DATE% %TIME% ==== >> logs\keepalive.log
python refresh_tokens.py >> logs\keepalive.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\keepalive.log
