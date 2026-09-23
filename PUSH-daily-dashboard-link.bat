@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"
echo ============================================================
echo   Point the Daily Dashboard button at the new Google Sheet copy
echo   of "Sales Data" (was the .xlsx). 3 files only.
echo ============================================================
if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock" del /f ".git\HEAD.lock"
git pull --rebase --autostash origin main
git add src/components/DashboardNav.tsx src/components/DashboardCards.tsx src/app/dashboard/daily/page.tsx
git -c user.email=mayank@nutriobox.com commit -m "Daily Dashboard: use native Google Sheet copy of Sales Data (robot-writable)" -- src/components/DashboardNav.tsx src/components/DashboardCards.tsx src/app/dashboard/daily/page.tsx
git push origin main
if errorlevel 1 (
  echo *** PUSH FAILED - read the message above. ***
  pause
  exit /b 1
)
echo.
echo SUCCESS. Vercel redeploys in ~1 min. Then Ctrl+F5 on opsdashboard.nutriobox.com
timeout /t 20 >nul
