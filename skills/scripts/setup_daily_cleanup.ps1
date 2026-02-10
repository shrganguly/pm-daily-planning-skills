# Windows Task Scheduler Setup for End-of-Day Cleanup
# Runs end_of_day_cleanup.py automatically at 11:45 PM every day

$TaskName = "ClaudeCode-DailyPlanCleanup"
$Description = "Automatically moves unchecked tasks to backlog at end of day"

# Get script path
$ScriptPath = Join-Path $PSScriptRoot "end_of_day_cleanup.py"
$PythonPath = (Get-Command python).Source

# Create action to run Python script
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`" --config" `
    -WorkingDirectory $PSScriptRoot

# Create trigger for 11:45 PM daily
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "11:45 PM"

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Register the task
Write-Host "Setting up daily cleanup task..." -ForegroundColor Cyan

try {
    # Check if task already exists
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

    if ($ExistingTask) {
        Write-Host "Task already exists. Updating..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Register new task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $Description `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -User $env:USERNAME `
        -RunLevel Highest

    Write-Host "`n✅ Successfully set up daily cleanup task!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: Daily at 11:45 PM"
    Write-Host "  Script: $ScriptPath"
    Write-Host "`nThe task will automatically:"
    Write-Host "  1. Scan today's daily plan at 11:45 PM"
    Write-Host "  2. Extract all unchecked tasks"
    Write-Host "  3. Move them to backlog for next day"
    Write-Host "`nYou can manage this task in Windows Task Scheduler."

    # Show next run time
    $Task = Get-ScheduledTask -TaskName $TaskName
    $NextRun = (Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime
    Write-Host "`nNext run: $NextRun" -ForegroundColor Yellow

} catch {
    Write-Host "`n❌ Failed to set up task: $_" -ForegroundColor Red
    Write-Host "`nYou may need to run PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}

Write-Host "`n---"
Write-Host "To manually run cleanup now (for testing):" -ForegroundColor Cyan
Write-Host "  python `"$ScriptPath`" --config"
Write-Host "`nTo remove this task:" -ForegroundColor Cyan
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
