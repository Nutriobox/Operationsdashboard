@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DEBUG ADDON %DATE% %TIME% ==== > logs\debug_addon.log
python debug_addon.py >> logs\debug_addon.log 2>&1
echo DEBUG_EXIT=%ERRORLEVEL% >> logs\debug_addon.log
type logs\debug_addon.log
echo.
echo Done. Log: logs\debug_addon.log
pause
