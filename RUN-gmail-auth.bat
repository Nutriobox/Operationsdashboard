@echo off
cd /d "%~dp0"
echo Running Gmail re-auth...
echo (A browser window will open - sign in as mayank@nutriobox.com and click Allow)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { .\scripts\get-gmail-refresh-token.ps1 } *>&1 | Tee-Object -FilePath .\gmail-auth.log"
echo.
echo ==== script exit code %ERRORLEVEL% ====
echo This window will stay open. Take a screenshot if anything looks wrong.
pause
