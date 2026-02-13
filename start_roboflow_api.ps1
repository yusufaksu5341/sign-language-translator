param(
    [string]$ApiKey = $env:ROBOFLOW_API_KEY,
    [string]$ModelId = "turk-isaret-dili/2",
    [string]$DatasetPath = "dataset1",
    [int]$Port = 8000
)

$defaultApiKey = "p6t4i9gco8ZGaA3Y1i26"

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $ApiKey = $defaultApiKey
}

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Write-Host "Roboflow API key gerekli. Cikis yapiliyor." -ForegroundColor Red
    exit 1
}

Write-Host "API baslatiliyor..." -ForegroundColor Cyan
Write-Host "Model: $ModelId"
Write-Host "Dataset: $DatasetPath"
Write-Host "Port: $Port"

$args = @(
    "serve_inference.py",
    "--api-key", $ApiKey,
    "--model-id", $ModelId,
    "--dataset", $DatasetPath,
    "--host", "127.0.0.1",
    "--port", "$Port"
)

& $pythonExe @args