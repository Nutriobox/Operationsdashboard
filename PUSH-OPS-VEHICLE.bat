@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"
echo ============================================================
echo   Publish corrected Vehicle Monitoring data to Ops Hub
echo ============================================================
if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock" del /f ".git\HEAD.lock"

echo.
echo Staging ONLY the two vehicle-monitoring public files...
git add -- public/vehicle-monitoring-data.json public/vehicle-monitoring-dashboard.html

echo.
echo Staged files:
git diff --cached --name-only
echo.

git commit -m "Vehicle monitoring: corrected 14-18 Aug data (10:00-19:00 window), honest per-date active count + footnote"
if errorlevel 1 (
  echo Nothing to commit or commit failed. See message above.
)
if exist ".git\index.lock" del /f ".git\index.lock"

echo.
echo Pushing to origin/main (Vercel auto-deploys)...
git push origin main
if errorlevel 1 (
  echo.
  echo *** PUSH FAILED. If it says non-fast-forward, tell Claude. ***
  echo If it asks you to sign in to GitHub, complete it and run this again.
  pause
  exit /b 1
)
echo.
echo === Recent history ===
git log --oneline -3
echo.
echo ============================================================
echo   SUCCESS. Vercel redeploys in ~1 min. Then hard-refresh:
echo   opsdashboard.nutriobox.com/dashboard/vehicle-monitoring
echo   (Ctrl+F5 to bypass cache)
echo ============================================================
pause
