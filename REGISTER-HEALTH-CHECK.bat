@echo off
title NutrioBox - Register Health Check Task

REM Registers a normal user-level task - no admin rights, no UAC prompt.

cd /d "%~dp0"

echo ============================================================
echo  Registering NutrioboxHealthCheck  (daily 09:35)
echo ============================================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\Register-HealthCheck.ps1"

echo.
pause
