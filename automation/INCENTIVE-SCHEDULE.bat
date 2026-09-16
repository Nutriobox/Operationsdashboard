@echo off
REM Register the three incentive fills as Windows scheduled tasks.
REM Run ONCE, only after a clean per-script validation:
REM   python incentive_delay.py   --headed --dry-run --monday <last-Monday>
REM   python incentive_weekly.py  --headed --dry-run --monday <last-Monday>
REM   python incentive_monthly.py --headed --dry-run --month  <YYYY-MM>
REM Finish the VALIDATE stubs (ratings M2, feedback M8, AOV M6) BEFORE scheduling
REM those metrics - until then those scripts fail-closed. Then DISABLE the Claude
REM twins (incentive--weekly-metrics-first-monday, incentive--monthly-metrics-1st-of-month,
REM incentive-delay-metrics-weekly-wed) in the SAME pass.
setlocal
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
if not exist logs mkdir logs
set A=C:\Users\hp\Downloads\Operationsdashboard\automation
schtasks /create /tn "NutrioBox-Incentive-Delay"   /sc weekly  /d WED /st 05:00 /f /tr "%A%\run_incentive_delay.bat"   >nul
schtasks /create /tn "NutrioBox-Incentive-Weekly"  /sc weekly  /d MON /st 15:30 /f /tr "%A%\run_incentive_weekly.bat"  >nul
schtasks /create /tn "NutrioBox-Incentive-Monthly" /sc monthly /d 1   /st 13:00 /f /tr "%A%\run_incentive_monthly.bat" >nul
for %%T in (NutrioBox-Incentive-Delay NutrioBox-Incentive-Weekly NutrioBox-Incentive-Monthly) do (
  schtasks /query /tn "%%T" /fo LIST 2>&1 | findstr /i "TaskName Next Status"
)
echo.
pause
