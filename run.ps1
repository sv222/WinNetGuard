# Firewall Manager - Quick Launch Script (PowerShell)
# Automatically requests administrator privileges if needed

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\pythonw.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run setup first:"
    Write-Host "  1. python -m venv .venv"
    Write-Host "  2. .venv\Scripts\pip install -r requirements.txt"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Run with pythonw.exe (no console window)
Start-Process -FilePath ".venv\Scripts\pythonw.exe" -ArgumentList "main.py" -WindowStyle Hidden

