$ErrorActionPreference = "SilentlyContinue"

$Ports = @(8000, 5173, 5174, 5175, 5176, 5177, 5178, 5179)

function Get-PortProcessIds {
    param([int]$Port)

    $pattern = '^\s*TCP\s+\S+:{0}\s+\S+\s+LISTENING\s+(\d+)$' -f $Port
    netstat -ano -p TCP |
        Select-String -Pattern $pattern |
        ForEach-Object { [int]$_.Matches[0].Groups[1].Value } |
        Select-Object -Unique
}

foreach ($port in $Ports) {
    $owners = Get-PortProcessIds -Port $port
    if ($owners) {
        Write-Host "Port $port is listening. Process ID: $($owners -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "Port $port is not listening." -ForegroundColor Yellow
    }
}
