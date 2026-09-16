@echo off
REM Register the Node Offer Tracker as a Windows task, run it once to verify, and
REM report the discount task's status. Results -> logs\offer_discount_setup.log
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set LOG=logs\offer_discount_setup.log
set OT=C:\Users\hp\Documents\Claude\Scheduled\daily-offer-tracker\playwright\run-daily.bat
echo ==== OFFER+DISCOUNT SETUP %DATE% %TIME% ==== > "%LOG%"
if exist "%OT%" (echo run-daily.bat FOUND >> "%LOG%") else (echo run-daily.bat MISSING >> "%LOG%")
schtasks /create /tn "NutrioBox-OfferTracker" /sc daily /st 04:09 /f /tr "\"%OT%\"" >> "%LOG%" 2>&1
schtasks /query /tn "NutrioBox-OfferTracker" /fo LIST 2>&1 | findstr /i "TaskName Next Status" >> "%LOG%"
echo ---- discount task (NutriboxDiscountFetch) status ---- >> "%LOG%"
schtasks /query /tn "NutriboxDiscountFetch" /fo LIST 2>&1 | findstr /i "TaskName Next Status" >> "%LOG%"
echo ---- running Offer Tracker once (verify) ---- >> "%LOG%"
schtasks /run /tn "NutrioBox-OfferTracker" >> "%LOG%" 2>&1
echo ==== DONE ==== >> "%LOG%"
