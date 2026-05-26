@echo off
cd /d "C:\Users\mayank\Documents\GitHub\Operationsdashboard"

echo =====================================================
echo  Deploy Claude changes (v2 - recovers from bad index)
echo =====================================================
echo.

echo === 1. Cleanup stale lock ===
if exist ".git\index.lock" del /f ".git\index.lock"

echo.
echo === 2. Backup my 2 text-file edits (icons are untracked, survive reset) ===
if not exist "_claude_backup" mkdir "_claude_backup"
copy /Y "src\app\layout.tsx" "_claude_backup\layout.tsx"
copy /Y "src\components\Navbar.tsx" "_claude_backup\Navbar.tsx"
echo.

echo === 3. Drop the bad stash from prior failed attempt ===
git stash drop stash@{0}
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 4. Force the repo back to a clean HEAD state ===
git reset --hard HEAD
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 5. Status after reset (should be near-empty, plus my untracked PNGs) ===
git status --short
echo.

echo === 6. Restore my text-file edits over the freshly-reset files ===
copy /Y "_claude_backup\layout.tsx" "src\app\layout.tsx"
copy /Y "_claude_backup\Navbar.tsx" "src\components\Navbar.tsx"
echo.

echo === 7. Verify all 5 files exist on disk ===
if not exist "src\app\layout.tsx" ( echo MISSING: src\app\layout.tsx & pause & exit /b 1 )
if not exist "src\components\Navbar.tsx" ( echo MISSING: src\components\Navbar.tsx & pause & exit /b 1 )
if not exist "src\app\icon.png" ( echo MISSING: src\app\icon.png & pause & exit /b 1 )
if not exist "src\app\apple-icon.png" ( echo MISSING: src\app\apple-icon.png & pause & exit /b 1 )
if not exist "public\favicon.png" ( echo MISSING: public\favicon.png & pause & exit /b 1 )
echo All 5 files present.
echo.

echo === 8. Sanity check: layout.tsx has new title ===
findstr /C:"Healthy, Tasty & Organic Food Cafes in Delhi NCR" "src\app\layout.tsx" >nul
if errorlevel 1 ( echo ERROR: new title not found in layout.tsx & pause & exit /b 1 )
echo OK.

echo === 9. Sanity check: Navbar.tsx no longer has Dashboard button ===
findstr /C:">Dashboard<" "src\components\Navbar.tsx" >nul
if not errorlevel 1 ( echo ERROR: Dashboard still in Navbar & pause & exit /b 1 )
echo OK.
echo.

echo === 10. Stage only my 5 files ===
git add src/app/layout.tsx src/components/Navbar.tsx src/app/icon.png src/app/apple-icon.png public/favicon.png
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo === 11. Staged diff stat (should be exactly 5 files) ===
git diff --cached --stat
echo.

echo === 12. Pull latest origin/main with rebase ===
git pull --rebase origin main
if errorlevel 1 ( echo PULL FAILED & pause & exit /b 1 )
echo.

echo === 13. Commit ===
git commit -m "Update tab title and favicon to match nutriobox.com; remove Dashboard nav button"
if errorlevel 1 ( echo COMMIT FAILED & pause & exit /b 1 )
echo.

echo === 14. Push to origin/main ===
git push origin main
if errorlevel 1 ( echo PUSH FAILED & pause & exit /b 1 )
echo.

echo === 15. Cleanup backup folder ===
rmdir /S /Q "_claude_backup"
echo.

echo =====================================================
echo  SUCCESS. Railway will redeploy in ~1 minute.
echo  Refresh operationsdashboard.nutriobox.com after that.
echo =====================================================
pause
