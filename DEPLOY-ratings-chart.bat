@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

echo =====================================================
echo  Deploy: merged Ratings chart + weekly-trend date fix
echo  (commits ONLY src\app\dashboard\ratings\page.tsx)
echo =====================================================
echo.

if exist ".git\index.lock" del /f ".git\index.lock"

echo === 1. Sanity check: the new merged chart code is present ===
findstr /C:"Weekly trend" "src\app\dashboard\ratings\page.tsx" >nul
if errorlevel 1 ( echo ERROR: merged-chart code not found in page.tsx & pause & exit /b 1 )
echo OK.
echo.

echo === 2. Stage ONLY the ratings page (ignores the harmless CRLF noise on other files) ===
git add -- src/app/dashboard/ratings/page.tsx
echo.

echo === 3. Show what will be committed (should be exactly 1 file) ===
git diff --cached --stat
echo.

echo === 4. Commit ===
git commit -m "Ratings: merge by-outlet + weekly-trend into one chart with view toggle; fix IST date filter"
if errorlevel 1 ( echo NOTHING TO COMMIT or COMMIT FAILED & pause & exit /b 1 )
echo.

echo === 5. Sync with origin/main (autostash keeps the CRLF noise out of the way) ===
git pull --rebase --autostash origin main
if errorlevel 1 ( echo PULL/REBASE FAILED - resolve manually & pause & exit /b 1 )
echo.

echo === 6. Push ===
git push origin main
if errorlevel 1 ( echo PUSH FAILED ^(check GitHub login^) & pause & exit /b 1 )
echo.

echo =====================================================
echo  SUCCESS. Railway will redeploy in ~1 minute.
echo  Then hard-refresh opsdashboard.nutriobox.com/dashboard/ratings
echo  (Ctrl+F5).
echo =====================================================
pause
