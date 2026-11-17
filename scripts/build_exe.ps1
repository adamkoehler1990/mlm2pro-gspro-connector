# Builds a one-file Windows executable of the MLM2PRO -> GSPro connector.
# Run in YOUR normal PowerShell (not elevated):
#   powershell -ExecutionPolicy Bypass -File "scripts\build_exe.ps1"
#
# Output: dist\mlm2pro-gspro-connector.exe
#
# The .exe bundles Python + bleak + cryptography, so end users do NOT need
# Python installed. Ship the .exe on a GitHub Release.

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = 'C:\Python315\python.exe' }
if (-not (Test-Path $py)) { throw "python not found - edit this script." }

Write-Host "Installing build dependencies (bleak, cryptography, pyinstaller)..."
& $py -m pip install --upgrade pyinstaller bleak cryptography

Write-Host "Building one-file executable..."
& $py -m PyInstaller `
    --onefile `
    --name mlm2pro-gspro-connector `
    --console `
    mlm2pro_bridge.py

Write-Host ""
Write-Host "Done. Executable:"
Write-Host "  $root\dist\mlm2pro-gspro-connector.exe"
Write-Host ""
Write-Host "Run it like the script, e.g.:"
Write-Host "  .\dist\mlm2pro-gspro-connector.exe --service --club 7i"
