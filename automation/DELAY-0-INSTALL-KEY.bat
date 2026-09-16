@echo off
setlocal enabledelayedexpansion
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
if not exist secrets mkdir secrets

echo ==== DELAY KEY INSTALL %DATE% %TIME% ==== > logs\delay.log

REM ---- 1. locate the newest service-account key in Downloads -------------
set "KEY="
for /f "delims=" %%F in ('dir /b /o-d "%USERPROFILE%\Downloads\nutriobox-ratings-*.json" 2^>nul') do (
  if not defined KEY set "KEY=%USERPROFILE%\Downloads\%%F"
)

if not defined KEY (
  echo.
  echo   Could not find nutriobox-ratings-*.json in %USERPROFILE%\Downloads
  echo   If you moved or renamed it, drop it at:
  echo     %CD%\secrets\nutriobox-sa.json
  echo   and run DELAY-1-SELFTEST.bat instead.
  echo.
  pause
  exit /b 1
)

echo Found key: !KEY!
echo Found key: !KEY! >> logs\delay.log

REM ---- 2. move it into place --------------------------------------------
move /y "!KEY!" "secrets\nutriobox-sa.json" >nul
if errorlevel 1 (
  echo   FAILED to move the key into secrets\ - is it open in another program?
  pause
  exit /b 1
)
echo Installed: %CD%\secrets\nutriobox-sa.json
echo Installed to secrets\nutriobox-sa.json >> logs\delay.log

REM ---- 3. dependencies ---------------------------------------------------
python -c "import google.oauth2.service_account, googleapiclient" 2>nul
if errorlevel 1 (
  echo Installing Google API client libraries...
  python -m pip install --quiet google-api-python-client google-auth >> logs\delay.log 2>&1
)

REM ---- 4. self-test -------------------------------------------------------
echo.
echo Running the self-test...
echo. >> logs\delay.log
python delay_dashboard.py --selftest >> logs\delay.log 2>&1
echo SELFTEST_EXIT=%ERRORLEVEL% >> logs\delay.log

echo.
powershell -NoProfile -Command "Get-Content logs\delay.log -Tail 30"
echo.
echo (full log: %CD%\logs\delay.log)
echo.
pause
