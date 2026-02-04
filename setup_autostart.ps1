# Setup Autostart with Admin Privileges
# This script creates a Task Scheduler task that runs the app at login with admin rights

$TaskName = "FirewallManagerAutostart"
$ScriptPath = $PSScriptRoot
$PythonExe = Join-Path $ScriptPath ".venv\Scripts\python.exe"
$MainScript = Join-Path $ScriptPath "main.py"

Write-Host "Setting up autostart for Firewall Manager..." -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task action (use pythonw.exe to hide console window)
$PythonWExe = Join-Path $ScriptPath ".venv\Scripts\pythonw.exe"
$Arguments = "$MainScript --minimized"
$Action = New-ScheduledTaskAction -Execute $PythonWExe -Argument $Arguments -WorkingDirectory $ScriptPath

# Create task trigger (at logon)
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

# Create task principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Firewall Manager - Auto-start with admin privileges" `
    -Force | Out-Null

Write-Host "✓ Autostart configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The app will now start automatically at login with admin privileges." -ForegroundColor White
Write-Host "No UAC prompt will appear." -ForegroundColor White
Write-Host ""
Write-Host "To remove autostart, run: remove_autostart.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
