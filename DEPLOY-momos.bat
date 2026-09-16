@echo off
setlocal
cd /d "%~dp0"
echo =====================================================
echo  Deploy Momos dashboard (self-hosted static HTML)
echo =====================================================
echo.
echo === 1. Clear stale git lock ===
if exist ".git\index.lock" del /f ".git\index.lock"
echo.
echo === 2. Stage ONLY the two momos files ===
git add src/components/DashboardCards.tsx public/nutriobox-momos-dashboard.html
if exist ".git\index.lock" del /f ".git\index.lock"
echo.
echo === 3. Staged diff (must show 2 files) ===
git diff --cached --stat
echo.
echo === 4. Commit ===
git commit -m "Momos dashboard: self-host static HTML in ops site; repoint card off Higgsfield"
if errorlevel 1 ( echo COMMIT FAILED ^(nothing to commit?^) & pause & exit /b 1 )
if exist ".git\index.lock" del /f ".git\index.lock"
echo.
echo === 5. Pull latest (rebase) ===
git pull --rebase origin main
if errorlevel 1 ( echo PULL/REBASE CONFLICT - resolve manually & pause & exit /b 1 )
if exist ".git\index.lock" del /f ".git\index.lock"
echo.
echo === 6. Push ===
git push origin main
if errorlevel 1 ( echo PUSH FAILED & pause & exit /b 1 )
echo.
echo === 7. Recent log ===
git log --oneline -3
echo.
echo =====================================================
echo  SUCCESS. Railway redeploys in ~1 min.
echo  Then refresh opsdashboard.nutriobox.com
echo =====================================================
pause
