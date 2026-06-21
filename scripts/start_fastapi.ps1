$action = New-ScheduledTaskAction `
    -Execute "C:\Projects\MT5PubSubFastApi\.venv\Scripts\python.exe" `
    -Argument "-m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --workers 1 --env-file .env.prod" `
    -WorkingDirectory "C:\Projects\MT5PubSubFastApi"

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName "MT5PubSubFastApi" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest