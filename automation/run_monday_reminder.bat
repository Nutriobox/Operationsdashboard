@echo off
REM Monthly portfolio-dashboard publish/reminder. Port of nutriobox-dashboard-monday-reminder.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== MONDAY REMINDER RUN %DATE% %TIME% ==== >> logs\monday_reminder.log
python monday_reminder.py %* >> logs\monday_reminder.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\monday_reminder.log
