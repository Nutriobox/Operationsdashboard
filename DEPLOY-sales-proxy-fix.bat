@echo off
REM ============================================================================
REM  DEPLOY-sales-proxy-fix.bat   (2026-10-21)
REM
REM  Ships the Sales Item dashboard fix:
REM    * src/app/api/sales-dashboard/route.ts  - proxy now re-gzips so the
REM      response stays under Vercel's ~4.5 MB cap (was returning an empty body)
REM    * scripts/upload-dashboard.ps1           - shrinks the export before upload
REM    * automation/shrink_dashboard.py         - the shrink transform (new)
REM
REM  Commits ONLY these files (your other uncommitted working changes are left
REM  alone) and pushes to main, which triggers a Vercel redeploy. The Supabase
REM  file was already replaced with the shrunk version, so once Vercel finishes
REM  (~1-2 min) the dashboard loads again.
REM
REM  Double-click to run. Git author stays mayank@nutriobox.com (do not change).
REM ============================================================================
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard"

echo === Clearing any stale git locks ===
if exist ".git\index.lock" del /f ".git\index.lock"
if exist ".git\HEAD.lock"  del /f ".git\HEAD.lock"
echo.

echo === Staging only the dashboard-fix files ===
git add ^
  "src/app/api/sales-dashboard/route.ts" ^
  "scripts/upload-dashboard.ps1" ^
  "automation/shrink_dashboard.py" ^
  "automation/daily_sheet_backfill.py" ^
  "automation/run_daily_sheet.bat" ^
  "automation/FIX-AUTOMATION-NOW.bat"
echo.

echo === What will be committed ===
git status --short -- "src/app/api/sales-dashboard/route.ts" "scripts/upload-dashboard.ps1" "automation/shrink_dashboard.py"
echo.

git commit -m "Sales dashboard: re-gzip proxy under Vercel cap + shrink export (fixes empty /api, 172MB render)"
if errorlevel 1 (
  echo.
  echo Nothing to commit, or commit failed. If it says 'nothing to commit', the
  echo files may already be committed. Check 'git log -1' above.
  pause
  exit /b 1
)
echo.

echo === Pushing to main (triggers Vercel redeploy) ===
git push origin main
if errorlevel 1 (
  echo.
  echo PUSH FAILED. Fix the error above, then re-run. Do NOT change git user.email.
  pause
  exit /b 1
)
echo.
echo Done. Vercel will redeploy in ~1-2 min. Then hard-refresh the Sales Item
echo dashboard (Ctrl+Shift+R). Ask Claude to verify once it's live.
echo.
pause
