# setup_windows_task.ps1
# Registers a Windows Scheduled Task to run Daily Market Update weekdays 30 mins after US close.

$TaskName = "DailyMarketSummaryUpdate"
$ProjectPath = $PSScriptRoot
$PythonPath = (Get-Command python).Source
$ScriptPath = Join-Path $ProjectPath "update.py"

# Calculate local time corresponding to 16:30 America/New_York
$NyTz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
$LocalTz = [System.TimeZoneInfo]::Local

$TestDate = [DateTime]::UtcNow.Date.AddHours(20).AddMinutes(30) # UTC approx for 16:30 EDT
$NyOffset = $NyTz.GetUtcOffset([DateTime]::UtcNow)
$LocalOffset = $LocalTz.GetUtcOffset([DateTime]::UtcNow)
$HourDiff = ($LocalOffset - $NyOffset).TotalHours

# We run scheduler.py or update.py
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " Setting up Windows Scheduled Task: $TaskName" -ForegroundColor Cyan
Write-Host " Project: $ProjectPath"
Write-Host " Python:  $PythonPath"
Write-Host "======================================================"

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectPath
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At (Get-Date "06:30 AM") # Adjusted in task settings or run via scheduler daemon

# Provide options to user
Write-Host "`nTo register the task to run automatically in Windows Task Scheduler:"
Write-Host "Option 1: Run scheduler.py in background:" -ForegroundColor Yellow
Write-Host "  python scheduler.py" -ForegroundColor Green
Write-Host "`nOption 2: Register task via schtasks (runs update.py weekdays):" -ForegroundColor Yellow
Write-Host "  schtasks /create /tn `"$TaskName`" /tr `"`"$PythonPath`" `"$ScriptPath`"`" /sc weekly /d MON,TUE,WED,THU,FRI /st 06:30 /f" -ForegroundColor Green
Write-Host "`n(Note: Adjust /st to match your local timezone equivalent of 16:30 New York time.)"
