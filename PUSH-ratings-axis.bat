@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

set BRANCH=ratings-yaxis-3-5
set WT=%TEMP%\nb-yaxis-worktree

echo =====================================================
echo  Push: Ratings weekly-trend y-axis 3.0 -^> 3.5
echo  Commit 47fd2fa, cherry-picked onto origin/main in a
echo  TEMPORARY worktree.
echo.
echo  Your main working tree, its 40 uncommitted files and
echo  both stashes are NOT touched by this script.
echo =====================================================
echo.

echo === 1. Clear stale lock files ===
if exist ".git\HEAD.lock"  del /f ".git\HEAD.lock"  && echo   removed HEAD.lock
if exist ".git\index.lock" del /f ".git\index.lock" && echo   removed index.lock
echo   done.
echo.

echo === 2. Fetch origin ===
git fetch origin
if errorlevel 1 ( echo FETCH FAILED ^(check network / GitHub login^) & pause & exit /b 1 )
echo.

echo === 3. Create temp worktree off origin/main ===
if exist "%WT%" git worktree remove --force "%WT%" >nul 2>&1
git branch -D %BRANCH% >nul 2>&1
git worktree add -b %BRANCH% "%WT%" origin/main
if errorlevel 1 ( echo WORKTREE CREATE FAILED & pause & exit /b 1 )
echo.

echo === 4. Cherry-pick the y-axis commit ===
pushd "%WT%"
git cherry-pick 47fd2fa
if errorlevel 1 (
  echo CHERRY-PICK FAILED - aborting cleanly, nothing pushed
  git cherry-pick --abort
  popd
  git worktree remove --force "%WT%"
  pause
  exit /b 1
)
echo.

echo === 5. Confirm exactly one file changed ===
git show --stat --oneline HEAD
echo.

echo === 6. Push the branch ===
git push -u origin %BRANCH%
if errorlevel 1 ( echo PUSH FAILED ^(check GitHub login^) & popd & pause & exit /b 1 )
popd
echo.

echo === 7. Remove the temp worktree ===
git worktree remove --force "%WT%"
echo.

echo =====================================================
echo  SUCCESS - branch "%BRANCH%" pushed to GitHub.
echo.
echo  This is NOT live yet. Open the repo on GitHub and
echo  merge the branch into main:
echo  https://github.com/Nutriobox/Operationsdashboard
echo.
echo  Railway redeploys ~1 min after the merge, then
echo  hard-refresh the ratings page with Ctrl+F5.
echo =====================================================
pause
