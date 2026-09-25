@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
REM Force UI mode so the Google sign-in window actually opens. Without this,
REM sheet_browser.login() short-circuits to "no login needed" and the automation
REM browser profile stays logged out (fixed 2026-09-25).
set NUTRIO_SHEETS_MODE=ui
echo.
echo   Opening a real browser window using the automation profile.
echo   Sign in to the Google account that can edit the Sales Data / KOT sheets
echo   (mayank@nutriobox.com).
echo.
echo   When the spreadsheet is on screen, come back here and press Enter
echo   (or just close the browser window - the login is saved either way).
echo.
python delay_dashboard.py --login
echo.
pause
