$ErrorActionPreference = "SilentlyContinue"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$ViteEntry = Join-Path $Root "node_modules\vite\bin\vite.js"
$NodeCandidates = @(
    (Join-Path $Root "node\node.exe"),
    "D:\nodejs\node.exe",
    "C:\Program Files\nodejs\node.exe"
)

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

function Show-PortStatus {
    param([int]$Port)

    $owners = Get-PortProcessIds -Port $Port
    if ($owners) {
        Write-Host "[WARN] Port $Port is in use. Process ID: $($owners -join ', ')" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Port $Port is free." -ForegroundColor Green
    }
}

function Get-PortProcessIds {
    param([int]$Port)

    $pattern = '^\s*TCP\s+\S+:{0}\s+\S+\s+LISTENING\s+(\d+)$' -f $Port
    netstat -ano -p TCP |
        Select-String -Pattern $pattern |
        ForEach-Object { [int]$_.Matches[0].Groups[1].Value } |
        Select-Object -Unique
}

Write-Host "Checking project environment..." -ForegroundColor Cyan
Write-Host "Project: $Root"

if (Test-Path -LiteralPath $Python) {
    $pythonVersion = & $Python --version
    Write-Host "[OK] Python: $pythonVersion"

    & $Python -c "import django; print('[OK] Django:', django.get_version())"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Django is not installed in .venv. Run: .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Red
    }
} else {
    Write-Host "[FAIL] Project Python was not found: $Python" -ForegroundColor Red
}

$Node = Find-Node
if ($Node) {
    $nodeVersion = & $Node --version
    Write-Host "[OK] Node: $nodeVersion ($Node)"
} else {
    Write-Host "[FAIL] node.exe was not found." -ForegroundColor Red
}

if (Test-Path -LiteralPath $ViteEntry) {
    Write-Host "[OK] Vite entry exists: $ViteEntry"
} else {
    Write-Host "[FAIL] Vite entry was not found. Run: npm.cmd install" -ForegroundColor Red
}

Show-PortStatus -Port 8000
Show-PortStatus -Port 5173

Write-Host "Check complete."
