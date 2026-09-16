# Registers the NutrioboxHealthCheck scheduled task (09:35 IST daily),
# alongside the existing NutrioboxDiscountFetch / NutrioboxDailyDeploy jobs.
#
# Runs as a NORMAL user task - no admin, no UAC prompt, no stored password.
# It therefore only fires while Satvik is logged in, which matches how the
# laptop is actually used and avoids putting an account password on disk.
#
# Run ONCE:
#   powershell -ExecutionPolicy Bypass -File scripts\Register-HealthCheck.ps1
#
# To remove it later:
#   Unregister-ScheduledTask -TaskName NutrioboxHealthCheck -Confirm:$false

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BatPath     = Join-Path $ProjectRoot 'RUN-health-check.bat'
$TaskName    = 'NutrioboxHealthCheck'

if (-not (Test-Path $BatPath)) {
    Write-Host "Missing $BatPath" -ForegroundColor Red
    exit 1
}

Write-Host "Registering '$TaskName' -> $BatPath"

$action = New-ScheduledTaskAction `
    -Execute $BatPath `
    -Argument '--quiet --noninteractive' `
    -WorkingDirectory $ProjectRoot

# 09:35 local time, every day. The 09:30 deploy needs a few minutes to land.
$trigger = New-ScheduledTaskTrigger -Daily -At '09:35'

# StartWhenAvailable makes a missed run (laptop asleep at 09:35) fire as soon
# as the machine is back - the exact failure mode from the 2026-06-06 incident.
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Task already exists - replacing it."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Daily NutrioBox Operations Dashboard health check and auto-fix (scripts/health-check.mjs).' | Out-Null

Write-Host ""
Write-Host "Registered. Verify with:" -ForegroundColor Green
Write-Host "  Get-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "Run it right now to test:" -ForegroundColor Green
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "Log: $env:USERPROFILE\Desktop\nutriobox-health-check.log"
