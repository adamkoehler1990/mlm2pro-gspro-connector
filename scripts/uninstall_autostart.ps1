# Removes the auto-start shortcut and stops the connector if it is running.
#   powershell -ExecutionPolicy Bypass -File "scripts\uninstall_autostart.ps1"

$ErrorActionPreference = 'SilentlyContinue'

$startup = [Environment]::GetFolderPath('Startup')
foreach ($name in @('MLM2PRO-GSPro Connector.lnk','MLM2PRO-GSPro Bridge.lnk')) {
    $lnk = Join-Path $startup $name
    if (Test-Path $lnk) { Remove-Item $lnk -Force }
}

# Remove any old Task Scheduler job from earlier versions.
Unregister-ScheduledTask -TaskName 'MLM2PRO-GSPro Bridge' -Confirm:$false

# Stop any running connector (compiled exe or python).
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe' OR Name='mlm2pro-gspro-connector.exe'" |
    Where-Object { $_.CommandLine -match 'mlm2pro_bridge\.py' -or $_.Name -eq 'mlm2pro-gspro-connector.exe' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Write-Host "Removed auto-start and stopped any running connector."
