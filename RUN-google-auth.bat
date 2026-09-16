@echo off
title NutrioBox - Google OAuth (Gmail + Sheets)
cd /d "%~dp0"

echo ============================================================
echo  Granting: gmail.readonly + gmail.send + spreadsheets.readonly
echo ============================================================
echo.
echo  A browser window will open.
echo  Sign in as mayank@nutriobox.com and approve ALL permissions.
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\get-google-refresh-token.ps1"

echo.
pause
