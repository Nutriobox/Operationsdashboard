@echo off
REM Fill/correct September 2026 in the OLD .xlsx "Sales Data" (1r9u4...) so it matches
REM the native. Uses the browser (UI) writer — the flaky one — with whole-row writes
REM and retries. If any dates come back FAILED, just run this again; it's re-runnable
REM and only rewrites the September rows.
setlocal
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== FILL XLSX SEP %DATE% %TIME% ==== >> logs\fill_xlsx_sep.log
python refresh_tokens.py >> logs\fill_xlsx_sep.log 2>&1
python fill_xlsx_sep.py >> logs\fill_xlsx_sep.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\fill_xlsx_sep.log
echo.
powershell -NoProfile -Command "Get-Content logs\fill_xlsx_sep.log -Tail 35"
pause
