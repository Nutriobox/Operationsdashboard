@echo off
REM One-off: capture the logged-in Petpooja session as storage_state JSON for AWS.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== EXPORT PP STATE %DATE% %TIME% ==== > logs\export_state.log
python export_pp_state.py >> logs\export_state.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\export_state.log
echo DONE. You can close this window.
