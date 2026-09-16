@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"
echo ============================================================
echo   Publishing Vehicle Monitoring Dashboard to the Ops Hub
echo ============================================================
echo.
echo Clearing any stale git locks...
if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock" del /f ".git\HEAD.lock"
echo.
echo Local commit to publish:
git log --oneline -1
echo.
echo origin/main is currently at:
git rev-parse --short origin/main
echo.
echo Pushing to GitHub (Railway will auto-deploy)...
git push origin main
if errorlevel 1 (
  echo.
  echo *** PUSH FAILED. Read the message above. ***
  echo If it says "non-fast-forward", tell Claude and it will rebase.
  echo If it asks to log in, complete the GitHub sign-in and run this again.
  pause
  exit /b 1
)
echo.
echo ============================================================
echo   SUCCESS. origin/main is now:
git rev-parse --short origin/main
echo   Railway redeploys in ~1 min, then hard-refresh:
echo   opsdashboard.nutriobox.com/dashboard/vehicle-monitoring
echo   (Ctrl+F5 to bypass browser cache)
echo ============================================================
pause
