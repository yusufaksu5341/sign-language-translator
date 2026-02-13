param(
    [string]$RoboflowApiKey = $env:ROBOFLOW_API_KEY,
    [string]$RoboflowModelId = "turk-isaret-dili/2",
    [string]$DatasetPath = "dataset1",
    [switch]$StartApi,
    [switch]$KeepApiRunning,
    [int]$ApiPort = 8000
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Write-Step($msg) {
    Write-Host "`n==== $msg ====" -ForegroundColor Cyan
}

function Get-PythonExe {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    return "python"
}

$pythonExe = Get-PythonExe
Write-Host "Python: $pythonExe"

Write-Step "Installing dependencies"
& $pythonExe -m pip install -r requirements.txt

if ([string]::IsNullOrWhiteSpace($RoboflowApiKey)) {
    Write-Host "ROBOFLOW_API_KEY is required." -ForegroundColor Red
    Write-Host "Use: .\run_all.ps1 -RoboflowApiKey <YOUR_KEY> -StartApi"
    exit 1
}

if (Test-Path $DatasetPath) {
    Write-Host "dataset1 found: $DatasetPath" -ForegroundColor Green
} else {
    Write-Host "dataset1 not found at: $DatasetPath" -ForegroundColor Yellow
}

if ($StartApi) {
    Write-Step "Starting Roboflow inference API"
    $apiArgs = @(
        "serve_inference.py",
        "--api-key", $RoboflowApiKey,
        "--model-id", $RoboflowModelId,
        "--dataset", $DatasetPath,
        "--host", "127.0.0.1",
        "--port", "$ApiPort"
    )
    $proc = Start-Process -FilePath $pythonExe -ArgumentList $apiArgs -PassThru

    Start-Sleep -Seconds 3
    $isListening = $false
    try {
        $conn = Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction Stop
        if ($conn) { $isListening = $true }
    } catch {
        $isListening = $false
    }

    if ($isListening) {
        Write-Host "API is listening on 127.0.0.1:$ApiPort" -ForegroundColor Green
    } else {
        Write-Host "API did not start correctly." -ForegroundColor Red
        try { Stop-Process -Id $proc.Id -Force } catch {}
        exit 1
    }

    if (-not $KeepApiRunning) {
        Write-Host "Stopping API (probe mode)."
        try { Stop-Process -Id $proc.Id -Force } catch {}
    } else {
        Write-Host "API process kept running (PID: $($proc.Id))."
    }
}

Write-Step "Done"
Write-Host "Next:"
Write-Host "1) chrome://extensions -> Load unpacked -> extension/"
Write-Host "2) Run API: $pythonExe serve_inference.py --api-key <KEY> --model-id $RoboflowModelId --dataset $DatasetPath --host 127.0.0.1 --port $ApiPort"
Write-Host "3) Open Google Meet and test overlay"
