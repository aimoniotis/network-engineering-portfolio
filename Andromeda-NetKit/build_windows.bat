@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe py -3 -m venv .venv
if errorlevel 1 exit /b 1

.venv\Scripts\python.exe -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Tkinter is unavailable. Reinstall Python with Tcl/Tk support enabled.
    exit /b 1
)

.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --log-level WARN AndromedaNetKit.spec
if errorlevel 1 exit /b 1

echo Build complete: %CD%\dist\AndromedaNetKit.exe
endlocal
