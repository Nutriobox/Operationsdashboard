@echo off
REM Momos Weekly - Playwright port of the Claude "nutriobox-momos-dashboard--weekly-update".
REM Appends the prior completed week to the self-hosted momos dashboard and pushes to GitHub.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== MOMOS WEEKLY RUN %DATE% %TIME% ==== >> logs\momos.log
python refresh_tokens.py >> logs\momos.log 2>&1
python momos_weekly.py --publish %* >> logs\momos.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\momos.log
