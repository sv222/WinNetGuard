# Remove Autostart Task
# This script removes the Task Scheduler task

$TaskName = "FirewallManagerAutostart"

Write-Host "Removing autostart for Firewall Manager..." -ForegroundColor Cyan
Write-Host ""

# Check if task exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✓ Autostart removed successfully!" -ForegroundColor Green
} else {
    Write-Host "⚠ Autostart task not found." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
