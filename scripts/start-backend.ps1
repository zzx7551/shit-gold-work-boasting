$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Manage = Join-Path $Root "backend\manage.py"
$Port = 8000

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

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Project Python was not found: $Python" -ForegroundColor Red
    Write-Host "Create it with: D:\anaconda_envs\anaconda_envs\claude\python.exe -m venv .venv"
    exit 1
}

if (-not (Test-Path -LiteralPath $Manage)) {
    Write-Host "Django manage.py was not found: $Manage" -ForegroundColor Red
    exit 1
}

if (Test-PortBusy -Port $Port) {
    Write-Host "Port $Port is already in use. Backend was not started again." -ForegroundColor Yellow
    Write-Host "Run stop-dev.bat to stop old dev services, or check the process manually."
    exit 1
}

Set-Location $Root
Write-Host "Starting Django backend: http://127.0.0.1:$Port" -ForegroundColor Green
& $Python $Manage runserver "127.0.0.1:$Port" --noreload
