@echo off
REM Weekly Dining/Delivery % fill. Port of weekly-petpooja-dining-delivery-update (Mon 8 AM).
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== DINING DELIVERY RUN %DATE% %TIME% ==== >> logs\dining_delivery.log
python refresh_tokens.py >> logs\dining_delivery.log 2>&1
python dining_delivery.py %* >> logs\dining_delivery.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\dining_delivery.log
