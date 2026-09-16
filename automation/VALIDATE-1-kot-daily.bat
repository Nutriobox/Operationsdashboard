@echo off
REM Validation for the Daily KOT port. WRITES NOTHING.
REM Runs the selftest (readers alive) then a dry-run for yesterday.
REM Output goes to logs\validate_kot_daily.log so it can be reviewed remotely.
chcp 65001 >nul
cd /d "%~dp0"

REM Python on Windows defaults stdout to cp1252; without this, printing any
REM non-ASCII character (arrows, rupee signs) raises UnicodeEncodeError and
REM masks the real error behind a traceback. Seen 2026-08-27.
set PYTHONIOENCODING=utf-8

set LOG=logs\validate_kot_daily.log
echo ================================================== >> %LOG%
echo [validate] START %date% %time% >> %LOG%

echo Running session check...
python refresh_tokens.py --check >> %LOG% 2>&1

echo Running selftest (writes nothing)...
python kot_daily.py --selftest >> %LOG% 2>&1
echo [validate] selftest exit=%ERRORLEVEL% >> %LOG%

echo Running dry-run (writes nothing)...
python kot_daily.py --dry-run >> %LOG% 2>&1
echo [validate] dryrun exit=%ERRORLEVEL% >> %LOG%

echo [validate] END %date% %time% >> %LOG%
echo.
echo Done. Results written to %LOG%
timeout /t 8
