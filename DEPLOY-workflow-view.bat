@echo off
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"
echo ============================================================
echo   Deploy: per-tile Workflow (eye) view
echo   Safe to re-run. Commits DashboardCards.tsx if changed,
echo   then always pushes any unpushed commit.
echo ============================================================
echo.

echo Clearing any stale git locks...
if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock" del /f ".git\HEAD.lock"
echo.

echo Staging the one changed file (no-op if already committed)...
git add src/components/DashboardCards.tsx
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo Committing if there is anything new (skips cleanly if not)...
git commit -m "Add per-tile workflow (eye) view sourced from scheduled tasks"
if errorlevel 1 (
  echo   ^(Nothing new to commit - the change is already committed. Continuing to push.^)
)
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo Confirming there is a commit to push...
git rev-list --count origin/main..HEAD > "%TEMP%\_ahead.txt"
set /p AHEAD=<"%TEMP%\_ahead.txt"
del "%TEMP%\_ahead.txt" 2>nul
echo   Commits ahead of origin/main: %AHEAD%
echo.

echo Pulling latest with rebase (autostash keeps your other local edits safe)...
git pull --rebase --autostash origin main
if errorlevel 1 (
  echo.
  echo *** PULL/REBASE HIT A CONFLICT. Tell Claude and it will help resolve. ***
  pause
  exit /b 1
)
if exist ".git\index.lock" del /f ".git\index.lock"
echo.

echo Pushing to GitHub (Vercel auto-deploys after)...
git push origin main
if errorlevel 1 (
  echo.
  echo *** PUSH FAILED. ***
  echo If it asked you to sign in to GitHub, complete the login and just run this file again.
  echo If it said "non-fast-forward", run this file again (it will rebase first).
  pause
  exit /b 1
)
echo.
echo ============================================================
echo   SUCCESS. origin/main is now:
git rev-parse --short origin/main
echo.
echo   Watch Vercel: a NEW deployment should appear and go Ready
echo   in ~1-2 min. It must NOT say "Blocked" (that only happened
echo   to the old ops@nutriobox.com commit - this one is mayank@).
echo.
echo   Then hard-refresh (Ctrl+F5):
echo   https://opsdashboard.nutriobox.com/dashboard
echo ============================================================
pause
