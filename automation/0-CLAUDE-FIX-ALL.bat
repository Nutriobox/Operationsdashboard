@echo off
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== CLAUDE FIX-ALL START %DATE% %TIME% ==== >> logs\fix_all.log
echo [1/3] weekly_sales >> logs\fix_all.log
call run_weekly_sales.bat >> logs\fix_all.log 2>&1
echo [2/3] kot_daily >> logs\fix_all.log
call run_kot_daily.bat >> logs\fix_all.log 2>&1
echo [3/3] daily_sheet >> logs\fix_all.log
call run_daily_sheet.bat >> logs\fix_all.log 2>&1
echo ==== CLAUDE FIX-ALL DONE %DATE% %TIME% ==== >> logs\fix_all.log
