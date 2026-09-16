@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
echo Harvesting Petpooja / Zomato / Swiggy tokens (headless)...
echo.
python refresh_tokens.py
echo.
pause
