@echo off
REM Weekly Discount Analytics refresh: last completed Mon-Sun week from Petpooja
REM  -> rebuild public/nutriobox-discount-dashboard.html -> git commit + push (Vercel).
REM Scheduled by DISCOUNT-WEEKLY-SCHEDULE.bat (Mon 06:00 IST). Runs headless.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DISCOUNT RUN %DATE% %TIME% ==== >> logs\discount.log
python discount_weekly.py --publish >> logs\discount.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\discount.log
