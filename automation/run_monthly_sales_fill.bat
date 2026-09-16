@echo off
REM Monthly Sales Fill - Playwright port of the Claude "nutriobox-weekly-petpooja-sales-fill".
REM Every Monday: month-to-date per-outlet Total Sales into the current month's block of
REM the "Monthly" tab (Sale + Avg/day). Reads the dashboard JSON; no single-outlet priming.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== MONTHLY SALES FILL RUN %DATE% %TIME% ==== >> logs\monthly_sales_fill.log
python refresh_tokens.py >> logs\monthly_sales_fill.log 2>&1
python monthly_sales_fill.py %* >> logs\monthly_sales_fill.log 2>&1
echo ==== EXIT %ERRORLEVEL% ==== >> logs\monthly_sales_fill.log
