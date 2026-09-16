@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set LOG=logs\setup.log
echo ============================================================ > "%LOG%"
echo   NutrioBox daily_data setup  %DATE% %TIME%                 >> "%LOG%"
echo ============================================================ >> "%LOG%"

echo [1/4] Python + pip diagnostics...
echo === python --version ===        >> "%LOG%" 2>&1
python --version                     >> "%LOG%" 2>&1
where python                         >> "%LOG%" 2>&1
python -m pip --version              >> "%LOG%" 2>&1

echo [2/4] Installing Python deps (requests, bs4, playwright, anthropic)...
python -m pip install -r requirements.txt >> "%LOG%" 2>&1

echo [3/4] Installing Playwright Chromium (first time can take a minute)...
python -m playwright install chromium >> "%LOG%" 2>&1

echo [4/4] Opening the sign-in browser.
echo.
echo   A browser will open with THREE tabs: Petpooja, Zomato, Swiggy.
echo   Sign in to each (Petpooja is the one that matters most), then come
echo   back to THIS window and press Enter.
echo.
python refresh_tokens.py --login
echo.
echo Harvesting + checking tokens...
python refresh_tokens.py --check >> "%LOG%" 2>&1
type "%LOG%" | find /i "petpooja"
echo.
echo Done. Full log: %LOG%
echo (You can close this window.)
pause
