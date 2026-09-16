@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set LOG=logs\deps.log
echo ============================================================ > "%LOG%"
echo   deps + environment check  %DATE% %TIME%                   >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo === python --version ===   >> "%LOG%" 2>&1
python --version               >> "%LOG%" 2>&1
echo === where python ===       >> "%LOG%" 2>&1
where python                   >> "%LOG%" 2>&1
echo === pip --version ===      >> "%LOG%" 2>&1
python -m pip --version        >> "%LOG%" 2>&1
echo === pip install -r requirements.txt === >> "%LOG%" 2>&1
python -m pip install -r requirements.txt >> "%LOG%" 2>&1
echo === playwright install chromium ===     >> "%LOG%" 2>&1
python -m playwright install chromium        >> "%LOG%" 2>&1
echo === import check ===       >> "%LOG%" 2>&1
python -c "import requests,bs4,playwright,config,claude_assist,dashboard_build,petpooja,browser_export,daily_data; print('IMPORTS_OK')" >> "%LOG%" 2>&1
echo DEPS_DONE_MARKER            >> "%LOG%" 2>&1
echo.
echo Finished. Log written to %LOG%
echo You can close this window.
pause
