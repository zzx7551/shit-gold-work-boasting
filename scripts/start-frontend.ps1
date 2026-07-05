$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$NodeCandidates = @(
    (Join-Path $Root "node\node.exe"),
    "D:\nodejs\node.exe",
    "C:\Program Files\nodejs\node.exe"
)
$ViteEntry = Join-Path $Root "node_modules\vite\bin\vite.js"
$Port = 5173

function Find-Node {
    foreach ($candidate in $NodeCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $cmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    return $null
}

function Get-PortProcessIds {
    param([int]$Port)

    $pattern = '^\s*TCP\s+\S+:{0}\s+\S+\s+LISTENING\s+(\d+)$' -f $Port
    netstat -ano -p TCP |
        Select-String -Pattern $pattern |
        ForEach-Object { [int]$_.Matches[0].Groups[1].Value } |
        Select-Object -Unique
}

function Test-PortBusy {
    param([int]$Port)
    return [bool](Get-PortProcessIds -Port $Port)
}

$Node = Find-Node
if (-not $Node) {
    Write-Host "node.exe was not found. Install Node.js to D:\nodejs or make sure node.exe is in PATH." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $ViteEntry)) {
    Write-Host "Vite entry was not found: $ViteEntry" -ForegroundColor Red
    Write-Host "Run this in the project root: npm.cmd install"
    exit 1
}

if (Test-PortBusy -Port $Port) {
    Write-Host "Port $Port is already in use. Frontend was not started again." -ForegroundColor Yellow
    Write-Host "Run stop-dev.bat to stop old dev services, or check the process manually."
    exit 1
}

Set-Location $Root
Write-Host "Starting Vue frontend: http://127.0.0.1:$Port" -ForegroundColor Green
& $Node $ViteEntry --host 127.0.0.1 --port $Port --strictPort
