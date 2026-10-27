@echo off
REM ============================================================
REM  Retire the laptop scheduled tasks that now run on AWS.
REM  These 10 are LIVE on AWS (Lambda + EventBridge) - disabling
REM  them here stops the laptop doing the same work twice.
REM
REM  Tasks intentionally LEFT RUNNING (not yet on AWS, or needed):
REM    NutrioBox-WeeklySales      (feeds the AWS delay dashboard)
REM    NutrioBox-MonthlySalesFill (feeds AWS incentive-monthly)
REM    NutrioBox-KOT-Weekly / KOT-Monthly / Momos-Weekly
REM    NutrioBox-DiscountWeekly / NutriboxDiscountFetch
REM    NutrioBox-MonthlyDashboard / MonthlyResync / WeeklyReport / MonthlyReminder
REM    NutrioBox-FailureWatch
REM    NutrioBox-SessionWatch / SessionWatch-PM  (keeps the login fresh - KEEP)
REM
REM  To re-enable any task later: schtasks /Change /TN "<name>" /ENABLE
REM ============================================================
setlocal
for %%T in (
  "NutrioBox-OfferTracker"
  "NutrioBox-DailySheet"
  "NutrioBox-KOT-Daily"
  "NutrioBox-Incentive-Delay"
  "NutrioBox-Incentive-Weekly"
  "NutrioBox-Incentive-Monthly"
  "NutrioBox-Delay-Weekly"
  "NutrioBox-Ratings-Weekly"
  "NutrioBox-DailyData-AM"
  "NutrioBox-DailyData-PM"
) do (
  echo Disabling %%T ...
  schtasks /Change /TN %%T /DISABLE
)
echo.
echo Done. The 10 migrated tasks are disabled; they now run only on AWS.
pause
