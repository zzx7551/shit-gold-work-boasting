$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendBat = Join-Path $Root "start-backend.bat"
$FrontendBat = Join-Path $Root "start-frontend.bat"

function Repair-ProcessPathEnvironment {
    $pathValue = [System.Environment]::GetEnvironmentVariable("Path", "Process")
    if (-not $pathValue) {
        $pathValue = [System.Environment]::GetEnvironmentVariable("PATH", "Process")
    }

    if ($pathValue) {
        [System.Environment]::SetEnvironmentVariable("Path", $pathValue, "Process")
        [System.Environment]::SetEnvironmentVariable("PATH", $null, "Process")
    }
}

Repair-ProcessPathEnvironment

Write-Host "Starting dev services..." -ForegroundColor Cyan
Write-Host "Backend: http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"

Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "`"$BackendBat`"" -WorkingDirectory $Root -WindowStyle Normal
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "`"$FrontendBat`"" -WorkingDirectory $Root -WindowStyle Normal

Write-Host "Two service windows were opened. Close a window to stop that service." -ForegroundColor Green
