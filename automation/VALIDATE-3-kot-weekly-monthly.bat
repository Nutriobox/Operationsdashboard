@echo off
REM Validation for the Weekly + Monthly KOT ports. WRITES NOTHING.
chcp 65001 >nul
cd /d "%~dp0"

REM Python on Windows defaults stdout to cp1252; without this, printing any
REM non-ASCII character (arrows, rupee signs) raises UnicodeEncodeError and
REM masks the real error behind a traceback. Seen 2026-08-27.
set PYTHONIOENCODING=utf-8

set LOG=logs\validate_kot_wm.log
echo ================================================== >> %LOG%
echo [validate] START %date% %time% >> %LOG%

echo Weekly KOT selftest...
python kot_weekly.py --selftest >> %LOG% 2>&1
echo [validate] weekly selftest exit=%ERRORLEVEL% >> %LOG%

echo Weekly KOT dry-run...
python kot_weekly.py --dry-run >> %LOG% 2>&1
echo [validate] weekly dryrun exit=%ERRORLEVEL% >> %LOG%

echo Monthly KOT selftest...
python kot_monthly.py --selftest >> %LOG% 2>&1
echo [validate] monthly selftest exit=%ERRORLEVEL% >> %LOG%

echo Monthly KOT dry-run...
python kot_monthly.py --dry-run >> %LOG% 2>&1
echo [validate] monthly dryrun exit=%ERRORLEVEL% >> %LOG%

echo [validate] END %date% %time% >> %LOG%
echo.
echo Done. Results written to %LOG%
timeout /t 8
