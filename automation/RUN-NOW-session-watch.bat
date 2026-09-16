@echo off
REM Manual run of the session watchdog (normally NutrioBox-SessionWatch @ 09:00/15:00).
REM Publishes reports/session-status.json and emails on degrade. Output -> logs\session_watch.log
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
if not exist logs mkdir logs
echo ==== MANUAL SESSION-WATCH RUN %DATE% %TIME% ==== >> logs\session_watch.log
python session_watch.py >> logs\session_watch.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\session_watch.log
echo Done. See logs\session_watch.log
pause
