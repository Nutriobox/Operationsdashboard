@echo off
cd /d "C:\Users\mayank\Documents\GitHub\Operationsdashboard"

echo =====================================================
echo  Deploy Claude changes (v3 - commit/pull/push only)
echo =====================================================
echo.

echo === 1. Cleanup stale lock ===
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 2. Defensive re-stage of the 5 target files ===
git add src/app/layout.tsx src/components/Navbar.tsx src/app/icon.png src/app/apple-icon.png public/favicon.png
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 3. Staged diff stat (must show 5 files only) ===
git diff --cached --stat
echo.

echo === 4. Commit ===
git commit -m "Update tab title and favicon to match nutriobox.com; remove Dashboard nav button"
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

echo === 7. Cleanup backup folder ===
if exist "_claude_backup" rmdir /S /Q "_claude_backup"
echo.

echo === 8. Final git log ===
git log --oneline -3
echo.

echo =====================================================
echo  SUCCESS. Railway will redeploy in ~1 minute.
echo  Refresh opsdashboard.nutriobox.com after that.
echo =====================================================
pause
