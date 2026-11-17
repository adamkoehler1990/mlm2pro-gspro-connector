# Registers the MLM2PRO -> GSPro connector to start hidden at Windows logon,
# using the per-user Startup folder (no admin, no Task Scheduler needed).
#
# Run in YOUR normal PowerShell:
#   powershell -ExecutionPolicy Bypass -File "scripts\install_autostart.ps1"
#
# Prefers the compiled dist\mlm2pro-gspro-connector.exe if you built one;
# otherwise falls back to pythonw.exe + mlm2pro_bridge.py.

$ErrorActionPreference = 'Stop'
$Club = '7i'                           # edit to your usual club if you like

$root = Split-Path $PSScriptRoot -Parent
$exe  = Join-Path $root 'dist\mlm2pro-gspro-connector.exe'

if (Test-Path $exe) {
    $target = $exe
    $args   = "--service --club $Club"
} else {
    $pyw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if (-not $pyw) { $pyw = 'C:\Python315\pythonw.exe' }
    if (-not (Test-Path $pyw)) { throw "pythonw.exe not found and no built .exe. Install Python or run scripts\build_exe.ps1." }
    $script = Join-Path $root 'mlm2pro_bridge.py'
    if (-not (Test-Path $script)) { throw "mlm2pro_bridge.py not found at repo root." }
    $target = $pyw
    $args   = ('"{0}" --service --club {1}' -f $script, $Club)
}

$startup = [Environment]::GetFolderPath('Startup')
$lnkPath = Join-Path $startup 'MLM2PRO-GSPro Connector.lnk'

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnkPath)
$sc.TargetPath       = $target
$sc.Arguments        = $args
$sc.WorkingDirectory = $root
$sc.WindowStyle      = 7               # minimized / hidden
$sc.Description      = 'MLM2PRO to GSPro connector'
$sc.Save()

Write-Host "Installed auto-start shortcut:"
Write-Host "  $lnkPath"
Write-Host "Target: $target $args"
Write-Host "It launches hidden at every logon. Log: $(Join-Path $root 'mlm2pro_bridge.log')"
