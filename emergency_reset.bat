@echo off
REM Emergency Reset - Double-click to remove all firewall rules
REM Automatically requests administrator privileges

echo Requesting administrator privileges...
powershell -Command "Start-Process python -ArgumentList 'emergency_reset.py' -Verb RunAs -WorkingDirectory '%CD%'"
