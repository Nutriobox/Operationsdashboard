@echo off
REM Weekly Consolidated Report - Playwright port of "weekly-petpooja-sales-report".
REM Pulls Petpooja Sub-Order + Petpooja KOT-delivery + Zomato funnel + Swiggy funnel
REM + Captain KOT, then writes D..AU (rows 5-23) of the current week's tab in the
REM Weekly Sales Report sheet through the signed-in Google Sheets UI (as mayank@).
REM
REM Prereqs (already present on this laptop):
REM   - secrets\tokens.json kept fresh by refresh_tokens.py (Petpooja session)
REM   - secrets\browser-profile signed in to Google (mayank@), Petpooja, and the
REM     Zomato + Swiggy partner portals. If any logs out:
REM       refresh_tokens.py --login   (Petpooja/Zomato/Swiggy)
REM       DELAY-LOGIN.bat             (Google Sheets)
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== WEEKLY REPORT RUN %DATE% %TIME% ==== >> logs\weekly_report.log
python refresh_tokens.py >> logs\weekly_report.log 2>&1
python weekly_report.py %* >> logs\weekly_report.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\weekly_report.log
