@echo off
REM Validation for the Daily Dashboard port. WRITES NOTHING.
REM selftest = scrape + sanity gates only (no sheet access at all)
REM dry-run  = also locates the target row and previews B..U
chcp 65001 >nul
cd /d "%~dp0"

REM Python on Windows defaults stdout to cp1252; without this, printing any
REM non-ASCII character (arrows, rupee signs) raises UnicodeEncodeError and
REM masks the real error behind a traceback. Seen 2026-08-27.
set PYTHONIOENCODING=utf-8

set LOG=logs\validate_daily_sheet.log
echo ================================================== >> %LOG%
echo [validate] START %date% %time% >> %LOG%

echo Running selftest (scrape + gates, writes nothing)...
python daily_sheet.py --selftest >> %LOG% 2>&1
echo [validate] selftest exit=%ERRORLEVEL% >> %LOG%

echo Running dry-run (locates row, previews values, writes nothing)...
python daily_sheet.py --dry-run >> %LOG% 2>&1
echo [validate] dryrun exit=%ERRORLEVEL% >> %LOG%

echo [validate] END %date% %time% >> %LOG%
echo.
echo Done. Results written to %LOG%
timeout /t 8
