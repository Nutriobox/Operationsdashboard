@echo off
REM One-time setup: registers "NutrioBox-KeepAlive" to run every 4 hours, WAKE the
REM laptop from sleep to do it, and catch up as soon as possible if it was missed.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c \"C:\Users\hp\Downloads\Operationsdashboard\automation\run_keepalive.bat\"';" ^
  "$t = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(2) -RepetitionInterval (New-TimeSpan -Hours 4);" ^
  "$s = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -MultipleInstances IgnoreNew;" ^
  "Register-ScheduledTask -TaskName 'NutrioBox-KeepAlive' -Action $a -Trigger $t -Settings $s -Force | Out-Null;" ^
  "Get-ScheduledTask -TaskName 'NutrioBox-KeepAlive' | Get-ScheduledTaskInfo | Select-Object TaskName,NextRunTime | Format-List"
echo.
echo  Also turning on "Allow wake timers" for the current power plan (so WakeToRun works)...
powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_SLEEP RTCWAKE 1
powercfg /SETACTIVE SCHEME_CURRENT
echo.
echo  Done. Keep-alive runs every 4 hours. Log: logs\keepalive.log
pause
