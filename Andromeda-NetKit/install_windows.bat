@echo off
setlocal
cd /d "%~dp0"

call build_windows.bat
if errorlevel 1 exit /b 1

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\AndromedaNetKit"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT=%START_MENU%\Andromeda NetKit.lnk"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if errorlevel 1 exit /b 1
if not exist "%START_MENU%" mkdir "%START_MENU%"
if errorlevel 1 exit /b 1

copy /Y "dist\AndromedaNetKit.exe" "%INSTALL_DIR%\AndromedaNetKit.exe" >nul
if errorlevel 1 exit /b 1

powershell.exe -NoProfile -Command "$shell = New-Object -ComObject WScript.Shell; $shortcut = $shell.CreateShortcut((Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Andromeda NetKit.lnk')); $shortcut.TargetPath = (Join-Path $env:LOCALAPPDATA 'Programs\AndromedaNetKit\AndromedaNetKit.exe'); $shortcut.WorkingDirectory = (Join-Path $env:LOCALAPPDATA 'Programs\AndromedaNetKit'); $shortcut.Description = 'Andromeda NetKit'; $shortcut.Save()"
if errorlevel 1 exit /b 1

del "%START_MENU%\Network Diagnostics Suite.lnk" >nul 2>&1
echo Installed Andromeda NetKit. Find it in the Start menu.
endlocal
