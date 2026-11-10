# Run this yourself (not by Claude): installs watch-stuck-input.ps1 as a hidden logon task for the current user and starts it.
# Remove later with:  Unregister-ScheduledTask -TaskName 'Release stuck input (watchdog)' -Confirm:$false
$dir = Join-Path $env:LOCALAPPDATA 'ReleaseStuckCtrl'
New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'watch-stuck-input.ps1') (Join-Path $dir 'watch-stuck-input.ps1') -Force
$act = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $dir 'watch-stuck-input.ps1'))
$trg = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName 'Release stuck input (watchdog)' -Action $act -Trigger $trg -Settings $set -Description 'Releases Ctrl/Shift/Alt/Win or mouse buttons that stay down for several seconds' -Force | Select-Object TaskName, State
Start-ScheduledTask -TaskName 'Release stuck input (watchdog)'
