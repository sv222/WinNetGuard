@echo off
REM Firewall Manager - Quick Launch Script
REM Automatically requests administrator privileges if needed

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   1. python -m venv .venv
    echo   2. .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Run with pythonw.exe (no console window)
start "" ".venv\Scripts\pythonw.exe" main.py

