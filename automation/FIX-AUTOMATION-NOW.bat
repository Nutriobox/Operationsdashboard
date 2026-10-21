@echo off
REM ============================================================================
REM  FIX-AUTOMATION-NOW.bat   (added 2026-10-21)
REM
REM  One-time fix for the root cause of the 21 Oct miss: the NutrioBox-DailySheet
REM  10:45 task (and others) were NOT set to catch up a run missed while the
REM  laptop was off/asleep, so Windows silently skipped the day. This:
REM     1. Turns ON Task Scheduler history (so future misses are RECORDED).
REM     2. Applies StartWhenAvailable + WakeToRun + run-on-battery + retry to
REM        EVERY Nutriobox* task, via your existing HARDEN-SCHEDULED-TASKS.ps1.
REM     3. Prints NutrioBox-DailySheet's settings so you can see it stuck.
REM
REM  Double-click it ONCE. Approve the UAC prompt (admin is required to change
REM  task wake settings and to enable history). Safe to re-run.
REM ============================================================================
setlocal
cd /d "%~dp0"

REM --- self-elevate ---
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================================
echo  [1/3] Enabling Task Scheduler history
echo ============================================================
wevtutil sl "Microsoft-Windows-TaskScheduler/Operational" /e:true
if %errorlevel% EQU 0 (echo   history ENABLED) else (echo   could not enable history)
echo.

echo ============================================================
echo  [2/3] Hardening all Nutriobox tasks ^(run-when-missed, wake, battery^)
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0HARDEN-SCHEDULED-TASKS.ps1"
echo.

echo ============================================================
echo  [3/3] Verifying NutrioBox-DailySheet
echo ============================================================
powershell -NoProfile -Command "$s=(Get-ScheduledTask -TaskName 'NutrioBox-DailySheet').Settings; Write-Host ('  StartWhenAvailable = ' + $s.StartWhenAvailable); Write-Host ('  WakeToRun          = ' + $s.WakeToRun); $i=Get-ScheduledTaskInfo -TaskName 'NutrioBox-DailySheet'; Write-Host ('  Last run   = ' + $i.LastRunTime); Write-Host ('  Next run   = ' + $i.NextRunTime); Write-Host ('  Last result= ' + $i.LastTaskResult)"
echo.
echo Done. StartWhenAvailable=True means a missed 10:45 run now fires as soon as
echo the laptop is next powered on. Combined with the new 5-day backfill in
echo run_daily_sheet.bat, a missed day now recovers automatically.
echo.
pause
