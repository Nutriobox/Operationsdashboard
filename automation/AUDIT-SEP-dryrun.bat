@echo off
REM SAFE PREVIEW — reads every September 2026 row and prints exactly which cells
REM would be filled and which discount values would be corrected. Writes NOTHING.
setlocal
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== AUDIT (dry-run) %DATE% %TIME% ==== > logs\resync_sep.log
python refresh_tokens.py >> logs\resync_sep.log 2>&1
python resync_sep.py --dry-run >> logs\resync_sep.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\resync_sep.log
echo.
powershell -NoProfile -Command "Get-Content logs\resync_sep.log -Tail 60"
pause
