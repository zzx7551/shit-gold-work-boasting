$ErrorActionPreference = "Continue"

$Ports = @(8000, 5173, 5174, 5175, 5176, 5177, 5178, 5179)
$pidsToStop = @()

function Get-PortProcessIds {
    param([int]$Port)

    $pattern = '^\s*TCP\s+\S+:{0}\s+\S+\s+LISTENING\s+(\d+)$' -f $Port
    netstat -ano -p TCP |
        Select-String -Pattern $pattern |
        ForEach-Object { [int]$_.Matches[0].Groups[1].Value } |
        Select-Object -Unique
}

foreach ($port in $Ports) {
    $pidsToStop += Get-PortProcessIds -Port $port
}

$pidsToStop = $pidsToStop | Where-Object { $_ -and $_ -ne $PID } | Select-Object -Unique

if (-not $pidsToStop) {
    Write-Host "No dev services were found on ports 8000/5173-5179." -ForegroundColor Yellow
    exit 0
}

foreach ($processId in $pidsToStop) {
    Write-Host "Stopping process: $processId"
    taskkill.exe /PID $processId /T /F | Out-Host
}

Start-Sleep -Seconds 2

$remaining = @()
foreach ($port in $Ports) {
    $remaining += Get-PortProcessIds -Port $port
}
$remaining = $remaining | Select-Object -Unique

if ($remaining) {
    Write-Host "Some dev service processes are still listening: $($remaining -join ', ')" -ForegroundColor Yellow
    exit 1
}

Write-Host "Dev services stopped." -ForegroundColor Green
