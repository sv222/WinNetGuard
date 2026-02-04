@echo off
REM Firewall Manager - Initial Setup Script
REM Run this once to set up the environment

echo ========================================
echo Firewall Manager - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)
echo Virtual environment created.
echo.

REM Install dependencies
echo Installing dependencies...
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo You can now run the application with:
echo   - Double-click run.bat
echo   - Or: .venv\Scripts\python.exe main.py
echo.
echo Optional:
echo   - Setup autostart: setup_autostart.bat
echo   - Enable strict mode: strict_mode.bat
echo.
pause
