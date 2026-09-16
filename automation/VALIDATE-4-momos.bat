@echo off
REM Validation for the Momos Weekly port. WRITES NOTHING.
REM NOTE: this one is SLOW — it exports 7 daily CSVs from Petpooja via
REM Playwright (roughly 5-10 minutes). Leave the window open until it finishes.
REM
REM The most recently completed week may already be published, in which case the
REM script exits immediately with "already published" — that is a PASS (the
REM idempotency guard working), not a failure.
chcp 65001 >nul
cd /d "%~dp0"

REM Python on Windows defaults stdout to cp1252; without this, printing any
REM non-ASCII character (arrows, rupee signs) raises UnicodeEncodeError and
REM masks the real error behind a traceback. Seen 2026-08-27.
set PYTHONIOENCODING=utf-8

set LOG=logs\validate_momos.log
echo ================================================== >> %LOG%
echo [validate] START %date% %time% >> %LOG%

echo Running Momos dry-run (exports 7 CSVs, writes nothing)...
python momos_weekly.py --dry-run >> %LOG% 2>&1
echo [validate] dryrun exit=%ERRORLEVEL% >> %LOG%

echo [validate] END %date% %time% >> %LOG%
echo.
echo Done. Results written to %LOG%
timeout /t 8
