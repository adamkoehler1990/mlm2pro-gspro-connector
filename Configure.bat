@echo off
REM One-click setup for the MLM2PRO -> GSPro Connector.
REM Double-click this file to open the setup window.

cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0configure.py"
    goto :eof
)

if exist "C:\Python315\pythonw.exe" (
    start "" "C:\Python315\pythonw.exe" "%~dp0configure.py"
    goto :eof
)

echo Python was not found. Install Python 3.10+ from https://www.python.org/downloads/
echo (tick "Add Python to PATH" during install), then run this again.
pause
