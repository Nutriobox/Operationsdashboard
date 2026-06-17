@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo =====================================================
echo  Recover: undo the stuck merge, back to live version
echo =====================================================
echo.

set "GIT="
where git >nul 2>&1 && set "GIT=git"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" set "GIT=%ProgramFiles(x86)%\Git\cmd\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set "GIT=%%D\resources\app\git\cmd\git.exe"
if not defined GIT ( echo Could not find git.exe. & pause & exit /b 1 )

echo Cancelling the half-done merge...
"%GIT%" rebase --abort 2>nul

echo Resetting to the live version (origin/main)...
"%GIT%" reset --hard origin/main
if errorlevel 1 (
  echo RESET FAILED. Tell Claude what this says.
  pause
  exit /b 1
)
echo.
echo =====================================================
echo  Recovered. Your local copy now matches the live site.
echo  Nothing was pushed; the live dashboard is unchanged.
echo =====================================================
"%GIT%" log --oneline -1
pause
