@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Get-CimInstance Win32_Process ^| Where-Object {$_.CommandLine -match 'main\.pyc'} ^| ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}" >nul 2>&1
taskkill /IM electron.exe /F >nul 2>&1
rmdir /S /Q "%APPDATA%\electron" >nul 2>&1
py -3.11 main.pyc
