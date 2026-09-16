@echo off
REM NutrioBox Operations Dashboard - daily automated health check.
REM Invoked by the NutrioboxHealthCheck scheduled task at 09:35 IST.
REM Double-click to run it manually.

cd /d "%~dp0"

REM Two logs on purpose: one on the Desktop for Satvik, one inside the repo
REM folder so it can also be read remotely from a Cowork session if needed.
set "DESKLOG=%USERPROFILE%\Desktop\nutriobox-health-check.log"
set "REPOLOG=%~dp0health-check.log"

echo [%DATE% %TIME%] Starting health check... >> "%DESKLOG%"

node scripts\health-check.mjs >> "%DESKLOG%" 2>&1
set EXITCODE=%ERRORLEVEL%

echo [%DATE% %TIME%] Finished with exit code %EXITCODE%. >> "%DESKLOG%"
echo. >> "%DESKLOG%"

REM Keep the repo copy to the last run only, so it stays small.
copy /Y "%DESKLOG%" "%REPOLOG%" >nul 2>&1

if not "%1"=="--quiet" (
  echo.
  echo Health check finished with exit code %EXITCODE%.
  echo Log: %DESKLOG%
  echo.
  if "%2"=="" pause
)

exit /b %EXITCODE%
