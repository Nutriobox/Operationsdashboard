@echo off
setlocal
title NutrioBox Health Check - Setup

REM Runs in place, in whatever folder this .bat lives in.
REM As of 2026-08-22 that is C:\Users\hp\Downloads\Operationsdashboard,
REM which is the live repo (remote: github.com/Nutriobox/Operationsdashboard).

cd /d "%~dp0"

echo ============================================================
echo  NutrioBox Health Check - Setup
echo ============================================================
echo.
echo  Repo: %CD%
echo.

if not exist "package.json" (
  echo [ERROR] No package.json here. Run this from the repo root.
  pause
  exit /b 1
)

if not exist ".env.local" (
  echo [ERROR] No .env.local here - the health check needs the Supabase and Google keys.
  pause
  exit /b 1
)

echo [1/3] Checking Node...
call node -v
if errorlevel 1 (
  echo [ERROR] Node is not on PATH. Install Node 20+ and re-run.
  pause
  exit /b 1
)
echo.

echo [2/3] Installing Playwright ^(this takes a minute^)...
call npm install -D playwright
if errorlevel 1 (
  echo [ERROR] npm install failed. See the output above.
  pause
  exit /b 1
)
echo.

echo [3/3] Downloading the Chromium browser build...
call npx playwright install chromium
if errorlevel 1 (
  echo [ERROR] playwright install failed. See the output above.
  pause
  exit /b 1
)
echo.

echo ============================================================
echo  Setup complete.
echo.
echo  NEXT STEPS:
echo    1. Enable the Google Sheets API in Cloud Console.
echo    2. Double-click RUN-google-auth.bat       (grants the 3 scopes)
echo    3. Double-click REGISTER-HEALTH-CHECK.bat (creates the 09:35 job)
echo ============================================================
echo.
pause
