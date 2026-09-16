@echo off
REM Register the session watchdog as a Windows scheduled task.
REM
REM Runs twice daily at 09:00 and 15:00 IST — deliberately during working hours,
REM so that when a session needs a 3-minute manual sign-in you are awake to do
REM it, rather than finding out from a failed 04:00 job the next morning.
REM
REM Run this ONCE. It is safe to re-run (uses /f).
cd /d "%~dp0"

REM Python on Windows defaults stdout to cp1252; without this, printing any
REM non-ASCII character (arrows, rupee signs) raises UnicodeEncodeError and
REM masks the real error behind a traceback. Seen 2026-08-27.
set PYTHONIOENCODING=utf-8

schtasks /create /tn "NutrioBox-SessionWatch" /sc daily /st 09:00 /f ^
  /tr "cmd /c cd /d %~dp0 && python session_watch.py >> logs\session_watch.log 2>&1" ^
  >> logs\session_schedule.log 2>&1

schtasks /create /tn "NutrioBox-SessionWatch-PM" /sc daily /st 15:00 /f ^
  /tr "cmd /c cd /d %~dp0 && python session_watch.py >> logs\session_watch.log 2>&1" ^
  >> logs\session_schedule.log 2>&1

echo Registered NutrioBox-SessionWatch (09:00) and -PM (15:00).
echo.
echo Verify with:  schtasks /query /tn "NutrioBox-SessionWatch"
echo Test alerting with:  python session_watch.py --alert-test
pause
