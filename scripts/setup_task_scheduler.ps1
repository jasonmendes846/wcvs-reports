# WCVS Daily Report — Windows Task Scheduler Setup
# Run this PowerShell script as Administrator to schedule daily report generation

$TaskName = "WCVS-Daily-Report"
$ProjectRoot = "C:\Users\jimmy\Projects\wcvs-platform"
$PythonPath = (Get-Command python).Source
$LogDir = "$ProjectRoot\outputs\logs"

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Build the action: generate report, run QC, build website
$ActionScript = @"
$PythonPath -m src.report_engine.generate_report --compact --full >> "$LogDir\report.log" 2>&1
if (`$LASTEXITCODE -eq 0) {
    $PythonPath "$ProjectRoot\.kimi\skills\wcvs-report-engine\scripts\qc_validate.py" --date (Get-Date -Format "yyyy-MM-dd") --report-dir "$ProjectRoot\outputs\reports" --website-dir "$ProjectRoot\outputs\website" >> "$LogDir\qc.log" 2>&1
    $PythonPath -m src.website.builder >> "$LogDir\website.log" 2>&1
}
"@

$ActionScriptPath = "$ProjectRoot\scripts\daily-run.ps1"
$ActionScript | Out-File -FilePath $ActionScriptPath -Encoding UTF8

# Create task action
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ActionScriptPath`""

# Trigger: daily at 4:30 PM ET (after US market close)
$Trigger = New-ScheduledTaskTrigger -Daily -At "16:30"

# Settings: wake computer if asleep, run as soon as possible if missed
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Principal: run whether user is logged on or not
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest

# Register task
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Generate daily WCVS market valuation report, run QC, and rebuild website." -Force

Write-Host "✓ Task '$TaskName' scheduled successfully."
Write-Host "  Runs daily at: 4:30 PM ET"
Write-Host "  Project root:  $ProjectRoot"
Write-Host "  Logs:          $LogDir"
Write-Host ""
Write-Host "To test immediately, run:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "To remove the task:"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
