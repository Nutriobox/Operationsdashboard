@echo off
REM Weekly Petpooja Sales Sync - Playwright/HTTP port of the Claude
REM "petpooja-weekly-sales-sync" task. Refreshes the Petpooja session, pulls last
REM week's per-outlet Total Sales, and fills the Weekly tab of the Sales Data sheet.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== WEEKLY SALES RUN %DATE% %TIME% ==== >> logs\weekly_sales.log
python refresh_tokens.py >> logs\weekly_sales.log 2>&1
python weekly_sales_sync.py --auto-tab %* >> logs\weekly_sales.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\weekly_sales.log
