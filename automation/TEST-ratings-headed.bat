@echo off
REM One-time visible test: runs the ratings refresh with a visible browser so you
REM can confirm Swiggy/Google load while signed in. Uploads for real on success.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== HEADED TEST %DATE% %TIME% ====
python ratings.py --headed
echo ==== EXIT %ERRORLEVEL% ====
pause
