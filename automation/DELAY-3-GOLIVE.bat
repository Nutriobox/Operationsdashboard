@echo off
setlocal
REM Registers the weekly delay job. Run this ONLY after DELAY-2-DRYRUN.bat has
REM shown a sensible week. Remember to disable the Cowork task
REM `nutriobox-weekly-delay-dashboard` afterwards, or both will append the same week.

schtasks /create /tn "NutrioBox-Delay-Weekly" ^
  /tr "cmd /c C:\Users\hp\Downloads\Operationsdashboard\automation\run_delay.bat" ^
  /sc weekly /d WED /st 06:00 /f

if errorlevel 1 (
  echo.
  echo   Could not register the task. Try running this file as administrator.
  echo.
  pause
  exit /b 1
)

echo.
echo   Registered: NutrioBox-Delay-Weekly, Wednesdays 06:00
echo.
echo   NEXT: ask Claude to disable the Cowork task
echo         `nutriobox-weekly-delay-dashboard` (it runs Wed 06:04).
echo         If both stay on, the week gets appended twice.
echo.
schtasks /query /tn "NutrioBox-Delay-Weekly" /fo list | findstr /i "TaskName Next Status"
echo.
pause
