@echo off
setlocal
cd /d "%~dp0"
title ear (PC) + Nothing Ear (3) — setup

:: ================================================================
::  ONE-SHOT SETUP — ear (PC) with Ear (3) support (pre-patched)
::  Contents of this folder: patched res/, main.pyc, DB, launcher src
::  This script: Python 3.11 -> deps -> electron UI -> ear-pc.exe ->
::               desktop shortcut -> launch. Rerun-safe.
:: ================================================================
py -3.11 interface_v3_clean.py 
if not exist main.pyc ( echo [x] run from extracted folder & pause & exit /b 1 )

:: ---- [1/6] Python 3.11 (probe by output — py manager exit codes lie)
set "PYPROBE="
py -3.11 -c "print('PYOK')" > "%TEMP%\e3p.txt" 2>nul
set /p PYPROBE=<"%TEMP%\e3p.txt"
if not "%PYPROBE%"=="PYOK" (
  echo [1/6] installing Python 3.11...
  py install 3.11
  set "PYPROBE="
  py -3.11 -c "print('PYOK')" > "%TEMP%\e3p.txt" 2>nul
  set /p PYPROBE=<"%TEMP%\e3p.txt"
)
if not "%PYPROBE%"=="PYOK" (
  echo [x] no Python 3.11. Run: py install 3.11
  echo     or https://www.python.org/downloads/release/python-3119/
  pause & exit /b 1
)
echo [1/6] Python 3.11 OK

:: ---- [2/6] eel + requests
echo [2/6] pip eel + requests...
py -3.11 -m pip install --quiet --disable-pip-version-check eel requests

:: ---- [3/6] bluetooth (wheel cascade, git last resort)
call :btprobe
if "%BTPROBE%"=="BTOK" ( echo [3/6] bluetooth OK & goto electron )
echo [3/6] installing pybluez-edge...
py -3.11 -m pip install --quiet --disable-pip-version-check pybluez-edge
call :btprobe
if "%BTPROBE%"=="BTOK" ( echo       bluetooth OK & goto electron )
py -3.11 -m pip install --quiet --disable-pip-version-check PyBluezovenlab
call :btprobe
if "%BTPROBE%"=="BTOK" ( echo       bluetooth OK & goto electron )
py -3.11 -m pip install git+https://github.com/pybluez/pybluez.git
call :btprobe
if "%BTPROBE%"=="BTOK" ( echo       bluetooth OK & goto electron )
echo [x] bluetooth install failed. For git build install:
echo     Git: https://git-scm.com/download/win
echo     C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
pause & exit /b 1

:electron
:: ---- [4/6] electron UI (prebuilt, ~100MB, one time)
if exist "electron\electron.exe" (
  echo [4/6] electron OK
) else (
  echo [4/6] downloading electron UI...
  curl -L -o e.zip https://github.com/radiance-project/ear-pc/releases/download/1.0.6/electron.zip
  if errorlevel 1 ( echo [x] download failed & pause & exit /b 1 )
  rmdir /S /Q electron 2>nul
  tar -xf e.zip
  del e.zip
  if not exist "electron\electron.exe" ( echo [x] extract failed & pause & exit /b 1 )
)

:: ---- [5/6] build ear-pc.exe (Windows built-in csc)
echo [5/6] building ear-pc.exe...
set "CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" set "CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if exist "%CSC%" (
  if exist ear-pc.exe del ear-pc.exe
  "%CSC%" /nologo /target:winexe /out:ear-pc.exe /win32icon:icon.ico ^
    /r:System.Management.dll /r:System.Windows.Forms.dll ear-pc-launcher.cs
)
if exist ear-pc.exe (
  echo       ear-pc.exe built
) else (
  echo       csc unavailable/failed — writing run.bat fallback
  > run.bat (
    echo @echo off
    echo cd /d "%%~dp0"
    echo powershell -NoProfile -Command "Get-CimInstance Win32_Process ^| Where-Object {$_.CommandLine -match 'main\.pyc'} ^| ForEach-Object {Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}" ^>nul 2^>^&1
    echo taskkill /IM electron.exe /F ^>nul 2^>^&1
    echo rmdir /S /Q "%%APPDATA%%\electron" ^>nul 2^>^&1
    echo py -3.11 main.pyc
  )
)

:: ---- [6/6] identity beacon + desktop shortcut
> res\whoami.txt (
  echo SERVING FROM: %~dp0
  echo BUILD: v8
)
if exist ear-pc.exe (
  powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\ear (PC).lnk');$s.TargetPath='%~dp0ear-pc.exe';$s.WorkingDirectory='%~dp0';$s.IconLocation='%~dp0icon.ico';$s.Save()" >nul 2>&1
  echo [6/6] desktop shortcut: ear ^(PC^)
)

del "%TEMP%\e3p.txt" 2>nul
echo.
echo ================================================
echo  DONE. Starting app...
echo  Later: desktop shortcut "ear (PC)" or ear-pc.exe
echo  Scanner shows: Select your device [v8] / Nothing Ear (3)
echo ================================================
if exist ear-pc.exe ( start "" ear-pc.exe ) else ( call run.bat )
exit /b 0

:btprobe
set "BTPROBE="
py -3.11 -c "import bluetooth;print('BTOK')" > "%TEMP%\e3p.txt" 2>nul
set /p BTPROBE=<"%TEMP%\e3p.txt"
exit /b 0
