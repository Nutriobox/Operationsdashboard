@echo off
REM Double-click to harden the NutrioBox scheduled tasks. Self-elevates to admin.
setlocal
set "PS=%~dp0Harden-Schedules.ps1"

REM Re-launch elevated if not already admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%PS%' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS%"
