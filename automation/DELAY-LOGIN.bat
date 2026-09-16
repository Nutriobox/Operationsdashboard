@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
echo.
echo   Opening a real browser window using the automation profile.
echo   Sign in to the Google account that can see the Weekly Sales sheet
echo   (the same one you use for the ops dashboard sheets).
echo.
echo   When the spreadsheet is on screen, come back here and press Enter.
echo.
python delay_dashboard.py --login
echo.
pause
