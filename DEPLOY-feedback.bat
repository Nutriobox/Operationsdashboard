@echo off
REM ===================================================================
REM  Deploy the Customer Feedback dashboard (calendar / date-range ver)
REM  Uploads Downloads\NutrioBox_Feedback_Dashboard.html to Supabase
REM  Storage as reports/feedback-dashboard.html, which the site serves
REM  into the Customer Feedback tab.
REM ===================================================================
cd /d "C:\Users\mayank\Documents\GitHub\Operationsdashboard"
echo Deploying Customer Feedback dashboard to Supabase...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\upload-feedback-dashboard.ps1"
