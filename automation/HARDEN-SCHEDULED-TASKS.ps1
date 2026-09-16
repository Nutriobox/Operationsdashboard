# =====================================================================
#  HARDEN-SCHEDULED-TASKS.ps1
#  Makes every Nutriobox scheduled task survive a laptop that is NOT on
#  24/7, without changing WHAT each task runs or WHEN.
#
#  What it sets on each task:
#    * StartWhenAvailable   -> if the laptop was OFF/asleep at the scheduled
#                              time, the task runs as soon as you next power
#                              on (instead of being silently skipped).
#    * WakeToRun            -> wake the laptop from SLEEP to run, then let it
#                              sleep again. (Only works from sleep + plugged
#                              in; it CANNOT wake a fully powered-off laptop.)
#    * Run on battery       -> DisallowStartIfOnBatteries / StopIfGoingOnBatteries
#                              set to false, so unplugging doesn't skip a run.
#    * RestartCount = 2     -> if a run fails, retry twice, 10 min apart.
#    * ExecutionTimeLimit   -> 2h safety cap so a hung run can't block forever.
#    * MultipleInstances    -> IgnoreNew, so a slow run never stacks on itself.
#
#  Run ONCE, as Administrator. Safe to re-run. Read-only apart from the
#  task settings it prints. Double-click HARDEN-SCHEDULED-TASKS.bat to launch
#  it elevated.
# =====================================================================

$ErrorActionPreference = "Stop"

# Match both "NutrioBox-*" and the few legacy "Nutribox*/Nutriobox*" tasks.
$pattern = "Nutri*"

$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -like $pattern }

if (-not $tasks) {
    Write-Host "No scheduled tasks matched '$pattern'. Nothing to do." -ForegroundColor Yellow
    Write-Host "(Have the *-SCHEDULE.bat / REGISTER-ALL-PLAYWRIGHT.bat files been run yet?)"
    exit 0
}

Write-Host "Found $($tasks.Count) matching task(s). Applying reliability settings...`n" -ForegroundColor Cyan

$ok = 0
$fail = 0
foreach ($t in $tasks) {
    $name = $t.TaskName
    try {
        $settings = New-ScheduledTaskSettingsSet `
            -StartWhenAvailable `
            -WakeToRun `
            -DontStopOnIdleEnd `
            -RestartCount 2 `
            -RestartInterval (New-TimeSpan -Minutes 10) `
            -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
            -MultipleInstances IgnoreNew

        # Explicitly allow running / continuing on battery.
        $settings.DisallowStartIfOnBatteries = $false
        $settings.StopIfGoingOnBatteries     = $false

        Set-ScheduledTask -TaskName $name -TaskPath $t.TaskPath -Settings $settings | Out-Null
        Write-Host ("  [OK]   {0}" -f $name) -ForegroundColor Green
        $ok++
    }
    catch {
        Write-Host ("  [FAIL] {0} -> {1}" -f $name, $_.Exception.Message) -ForegroundColor Red
        $fail++
    }
}

Write-Host ""
Write-Host ("Done. {0} updated, {1} failed." -f $ok, $fail) -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: WakeToRun only wakes the laptop from SLEEP, and only if"
Write-Host "Windows power settings allow wake timers and it is plugged in."
Write-Host "A fully powered-OFF laptop cannot wake itself; those missed runs"
Write-Host "will instead run the moment you power the laptop back on"
Write-Host "(that is what StartWhenAvailable guarantees)."
