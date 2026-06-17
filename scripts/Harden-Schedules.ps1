# Makes the existing NutrioBox scheduled tasks far more resilient WITHOUT
# changing what they run or needing your password. For each task it enables:
#   - Run as soon as possible after a missed start (laptop was off/asleep)
#   - Wake the computer to run the task (works from sleep, not full shutdown)
#   - Keep running on battery / don't stop when switching to battery
#   - Retry up to 3 times, 5 minutes apart, if a run fails
#
# Run it by double-clicking Harden-Schedules.bat (it elevates automatically).

$ErrorActionPreference = 'Continue'

$taskNames = @(
    'NutrioboxDiscountFetch',
    'NutrioboxDailyDeploy',
    'NutrioboxDailyDeployPM'
)

Write-Host "=== Hardening NutrioBox scheduled tasks ===" -ForegroundColor Cyan

foreach ($name in $taskNames) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host ("[SKIP] Task '{0}' not found." -f $name) -ForegroundColor Yellow
        continue
    }

    $s = $task.Settings
    $s.StartWhenAvailable        = $true    # catch up missed runs
    $s.WakeToRun                 = $true    # wake from sleep to run
    $s.DisallowStartIfOnBatteries = $false  # allow on battery
    $s.StopIfGoingOnBatteries     = $false  # don't kill mid-run on battery
    $s.ExecutionTimeLimit        = 'PT1H'   # 1-hour cap so a hung run can't block the next
    $s.RestartCount              = 3        # retry on failure
    $s.RestartInterval           = 'PT5M'   # 5 minutes apart

    try {
        Set-ScheduledTask -TaskName $name -Settings $s -ErrorAction Stop | Out-Null
        Write-Host ("[OK]   '{0}': wake+catch-up+battery+retry enabled." -f $name) -ForegroundColor Green
    } catch {
        Write-Host ("[FAIL] '{0}': {1}" -f $name, $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done. Current settings:" -ForegroundColor Cyan
foreach ($name in $taskNames) {
    $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($t) {
        $t.Settings | Select-Object @{n='Task';e={$name}}, StartWhenAvailable, WakeToRun,
            DisallowStartIfOnBatteries, RestartCount | Format-List
    }
}
Write-Host "NOTE: WakeToRun only wakes the laptop from SLEEP. If it is fully" -ForegroundColor Yellow
Write-Host "      shut down at the scheduled time, the task still cannot run." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close"
