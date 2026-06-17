@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo =====================================================
echo  Deploy: weekly ratings line chart
echo =====================================================
echo.

set "GIT="
where git >nul 2>&1 && set "GIT=git"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" set "GIT=%ProgramFiles(x86)%\Git\cmd\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set "GIT=%%D\resources\app\git\cmd\git.exe"
if not defined GIT ( echo Could not find git.exe. Install Git for Windows, then re-run. & pause & exit /b 1 )
echo Using git: %GIT%
echo.

if exist ".git\index.lock" del /f ".git\index.lock"

echo === 1. Stage the changed files ===
"%GIT%" add src/app/dashboard/ratings/page.tsx src/app/api/ratings-history/route.ts
echo.

echo === 2. What will be committed ===
"%GIT%" diff --cached --stat
echo.

echo === 3. Commit ===
"%GIT%" commit -m "Ratings: weekly line chart with calendar week picker (all-outlet average)"
echo.

echo === 4. Sync with remote (autostash keeps other edits safe) ===
"%GIT%" pull --rebase --autostash origin main
if errorlevel 1 ( echo PULL FAILED - tell Claude what it says. & pause & exit /b 1 )
echo.

echo === 5. Push (triggers the host rebuild) ===
"%GIT%" push origin main
if errorlevel 1 ( echo PUSH FAILED - check GitHub sign-in. & pause & exit /b 1 )
echo.
echo =====================================================
echo  Done. The host rebuilds in a minute or two; open the
echo  Ratings tab and you'll see the weekly line chart.
echo =====================================================
pause
