@echo off
REM ============================================================
REM  Refresh the logged-in session the AWS automation uses.
REM  Run this when you get a "SessionExpired" / login alert, OR
REM  periodically (e.g. monthly) to keep it fresh.
REM
REM  If Petpooja/Google are logged OUT in the automation profile,
REM  first run DELAY-LOGIN.bat / TOKENS-LOGIN.bat to sign back in,
REM  THEN run this.
REM ============================================================
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
echo ==== REFRESH SESSION %DATE% %TIME% ==== > logs\refresh_session.log
echo Step 1: export logged-in session...
python export_pp_state.py >> logs\refresh_session.log 2>&1
echo Step 2: upload to AWS...
python upload_state.py >> logs\refresh_session.log 2>&1
type logs\refresh_session.log | findstr /C:"session:" /C:"uploaded" /C:"FAILED" /C:"ERROR"
echo.
echo DONE. If it says LOGGED_IN and "uploaded ... HTTP 200", AWS is refreshed.
pause
