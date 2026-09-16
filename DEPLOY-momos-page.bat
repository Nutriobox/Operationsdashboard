@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

echo =====================================================
echo  Deploy: Momos dashboard as in-app page (navbar + Back)
echo =====================================================
echo.

echo === 1. Clear stale lock ===
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 2. Stage ONLY the 2 momos-page files ===
git add src/app/dashboard/momos/page.tsx
git add src/components/DashboardCards.tsx
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 3. Staged diff stat (should list the 2 files) ===
git diff --cached --stat
echo.

echo === 4. Commit ===
git commit -m "Momos: serve as in-app dashboard page (Nutriobox navbar, logo->home, Back works)"
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
echo  SUCCESS. Redeploys in ~1 minute. Then hard-refresh:
echo  opsdashboard.nutriobox.com/dashboard  (Ctrl+F5)
echo  Click the Momos card - it should stay in one page
echo  with the Nutriobox navbar and a working Back button.
echo =====================================================
pause
