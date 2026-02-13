param(
    [switch]$Quick = $true,
    [switch]$ForceRebuild,
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

if ($Quick) {
    $datasetOut = "processed/sign_dataset_small.npz"
    $modelOut = "models/sign_classifier_small.joblib"
    $prepareArgs = @(
        "prepare_dataset.py",
        "--dataset", "tid_dataset",
        "--output", $datasetOut,
        "--sequence-len", "20",
        "--max-frames", "40",
        "--frame-size", "24"
    )
    $trainArgs = @(
        "train_model.py",
        "--input", $datasetOut,
        "--model", $modelOut,
        "--test-size", "0.2",
        "--min-samples-per-class", "2",
        "--max-classes", "150"
    )
    $indexArgs = @(
        "build_sign_index.py",
        "--dataset", "tid_dataset",
        "--output", "models/sign_index.npz",
        "--sequence-len", "20",
        "--max-frames", "40",
        "--frame-size", "24"
    )
} else {
    $datasetOut = "processed/sign_dataset.npz"
    $modelOut = "models/sign_classifier.joblib"
    $prepareArgs = @(
        "prepare_dataset.py",
        "--dataset", "tid_dataset",
        "--output", $datasetOut,
        "--frame-size", "32"
    )
    $trainArgs = @(
        "train_model.py",
        "--input", $datasetOut,
        "--model", $modelOut,
        "--test-size", "0.2",
        "--min-samples-per-class", "2",
        "--max-classes", "200"
    )
    $indexArgs = @(
        "build_sign_index.py",
        "--dataset", "tid_dataset",
        "--output", "models/sign_index.npz",
        "--frame-size", "32"
    )
}

if ($ForceRebuild -or -not (Test-Path $datasetOut)) {
    Write-Step "Preparing dataset features"
    & $pythonExe @prepareArgs
} else {
    Write-Host "Dataset already exists: $datasetOut"
}

if ($ForceRebuild -or -not (Test-Path $modelOut)) {
    Write-Step "Training model"
    & $pythonExe @trainArgs
} else {
    Write-Host "Model already exists: $modelOut"
}

if ($ForceRebuild -or -not (Test-Path "models/sign_index.npz")) {
    Write-Step "Building one-shot sign index"
    & $pythonExe @indexArgs
} else {
    Write-Host "Index already exists: models/sign_index.npz"
}

if ($StartApi) {
    Write-Step "Starting inference API"
    $apiArgs = @("serve_inference.py", "--model", $modelOut, "--index", "models/sign_index.npz", "--host", "127.0.0.1", "--port", "$ApiPort")
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
Write-Host "2) Run API: $pythonExe serve_inference.py --model $modelOut --host 127.0.0.1 --port $ApiPort"
Write-Host "3) Open Google Meet and test overlay"
