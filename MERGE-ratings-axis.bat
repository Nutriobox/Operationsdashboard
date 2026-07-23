@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

echo =====================================================
echo  MERGE: fast-forward origin/main to include the
echo  y-axis 3.0 -^> 3.5 commit, making it LIVE.
echo.
echo  This only moves the branch on GitHub. Your local
echo  main, its 4 local commits, the 40 uncommitted files
echo  and both stashes are NOT touched.
echo =====================================================
echo.

if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock"  del /f ".git\HEAD.lock"

echo === 1. Fetch latest refs ===
git fetch origin
if errorlevel 1 ( echo FETCH FAILED & pause & exit /b 1 )
echo.

echo === 2. Confirm this is a clean fast-forward ===
git merge-base --is-ancestor origin/main origin/ratings-yaxis-3-5
if errorlevel 1 (
  echo NOT a fast-forward - origin/main has moved on.
  echo Aborting; nothing pushed. Merge via a PR on GitHub instead.
  pause
  exit /b 1
)
echo   OK - origin/main is an ancestor, fast-forward is safe.
echo.

echo === 3. What will land on main ===
git log --oneline origin/main..origin/ratings-yaxis-3-5
git diff --stat origin/main origin/ratings-yaxis-3-5
echo.

echo === 4. Fast-forward main on GitHub ===
git push origin origin/ratings-yaxis-3-5:main
if errorlevel 1 ( echo PUSH FAILED ^(branch protection? GitHub login?^) & pause & exit /b 1 )
echo.

echo === 5. Verify ===
git fetch origin
git log --oneline -1 origin/main
echo.

echo =====================================================
echo  SUCCESS - main updated on GitHub. It is now LIVE
echo  once Railway finishes redeploying (~1 minute).
echo  Then hard-refresh the ratings page with Ctrl+F5.
echo =====================================================
pause
