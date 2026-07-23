@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

echo =====================================================
echo  Clear stale git lock files
echo  Run this if git reports:
echo    "Unable to create ... .git/index.lock: File exists"
echo    "cannot lock ref 'HEAD'"
echo  (Only run when no git command is actually running.)
echo =====================================================
echo.

if exist ".git\index.lock" ( del /f ".git\index.lock" && echo   removed index.lock ) else ( echo   index.lock  - not present )
if exist ".git\HEAD.lock"  ( del /f ".git\HEAD.lock"  && echo   removed HEAD.lock  ) else ( echo   HEAD.lock   - not present )
echo.

echo === Current repo state ===
git status --short --branch
echo.
echo Done.
pause
