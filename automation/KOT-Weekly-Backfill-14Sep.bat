@echo off
REM One-click backfill of Weekly KOT for Mon 14 Sep - Sun 20 Sep 2026.
REM The scheduled run on 21 Sep failed (Petpooja logged out). Run this ONLY AFTER:
REM   1) python refresh_tokens.py --login   (Petpooja / Zomato / Swiggy)
REM   2) DELAY-LOGIN.bat                    (Google profile as mayank@)
REM Creates + fills the "14th September - 20th September" tab, leftmost.
REM Safe to re-run: it refuses to duplicate an existing week.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
call run_kot_weekly.bat --monday 2026-09-14
echo.
echo ==== Backfill finished. Result: logs\kot_weekly.log (look for EXIT 0) ====
powershell -NoProfile -Command "Get-Content logs\kot_weekly.log -Tail 25"
pause
