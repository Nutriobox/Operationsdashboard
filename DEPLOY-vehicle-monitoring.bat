@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

echo =====================================================
echo  Deploy: Add Vehicle Monitoring Dashboard
echo =====================================================
echo.

echo === 1. Clear stale lock ===
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 2. Stage ONLY the 3 vehicle-monitoring files ===
git add public/vehicle-monitoring-dashboard.html
git add src/app/dashboard/vehicle-monitoring/page.tsx
git add src/components/DashboardCards.tsx
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 3. Staged diff stat (should list the 3 files) ===
git diff --cached --stat
echo.

echo === 4. Commit ===
git commit -m "Add Vehicle Monitoring Dashboard to Operations Hub"
if errorlevel 1 (
    echo COMMIT FAILED
    pause
    exit /b 1
)
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 5. Pull latest with rebase ===
git pull --rebase origin main
if errorlevel 1 (
    echo PULL FAILED - resolve conflicts manually
    pause
    exit /b 1
)
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 6. Push to origin/main ===
git push origin main
if errorlevel 1 (
    echo PUSH FAILED
    pause
    exit /b 1
)
echo.

echo === 7. Recent log ===
git log --oneline -3
echo.

echo =====================================================
echo  SUCCESS. Railway will redeploy in ~1 minute.
echo  Then refresh opsdashboard.nutriobox.com
echo =====================================================
pause
