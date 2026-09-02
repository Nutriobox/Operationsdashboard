@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"
echo ============================================================
echo   Publish Discount Analytics (public/nutriobox-discount-dashboard.html)
echo ============================================================
echo.
echo Clearing any stale git locks...
if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock" del /f ".git\HEAD.lock"
echo.
echo Commit waiting to publish:
git log --oneline -1
echo.
echo Author of that commit (must be mayank@nutriobox.com):
git log -1 --format="%%an <%%ae>"
echo.
echo Pushing to GitHub (Vercel auto-deploys)...
git push origin main
if errorlevel 1 (
  echo.
  echo *** PUSH FAILED. Read the message above. ***
  echo   - "non-fast-forward": pull/rebase then run this again.
  echo   - asks to log in: complete the GitHub sign-in and run this again.
  pause
  exit /b 1
)
echo.
echo ============================================================
echo   SUCCESS. Vercel redeploys in ~1 min, then hard-refresh:
echo   opsdashboard.nutriobox.com/dashboard/discount-analytics
echo   (Ctrl+F5 to bypass browser cache)
echo   This window closes automatically in 15 seconds.
echo ============================================================
timeout /t 15 >nul
