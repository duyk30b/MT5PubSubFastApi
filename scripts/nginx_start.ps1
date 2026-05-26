$action = New-ScheduledTaskAction `
    -Execute "C:\Programs\nginx\nginx.exe" `
    -WorkingDirectory "C:\Programs\nginx"

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName "Nginx" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest