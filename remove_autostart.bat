@echo off
REM Remove Autostart - Run this as administrator

echo Requesting administrator privileges...
powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0remove_autostart.ps1\"' -Verb RunAs"
