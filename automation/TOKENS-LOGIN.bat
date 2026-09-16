@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
echo.
echo   Opens a browser with three tabs: Petpooja, Zomato, Swiggy.
echo   Sign in to each one.
echo.
echo   IMPORTANT: come back to THIS window and press Enter while the
echo   browser is still open. Closing the browser first is now handled,
echo   but pressing Enter first is still the clean way.
echo.
python refresh_tokens.py --login
echo.
pause
