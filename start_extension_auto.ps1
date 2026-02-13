param(
    [string]$MeetUrl = "https://meet.google.com/",
    [string]$ExtensionPath = "extension",
    [switch]$StartLocalApi,
    [string]$ApiKey = $env:ROBOFLOW_API_KEY,
    [string]$ModelId = "turk-isaret-dili/2",
    [string]$DatasetPath = "dataset1",
    [int]$Port = 8000,
    [switch]$UseTempProfile = $true
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Resolve-ChromePath {
    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
    )

    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }

    return "chrome"
}

function Resolve-PythonPath {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    return "python"
}

$extensionFullPath = Join-Path $PSScriptRoot $ExtensionPath
if (-not (Test-Path $extensionFullPath)) {
    Write-Host "Extension path bulunamadi: $extensionFullPath" -ForegroundColor Red
    exit 1
}

if ($StartLocalApi) {
    $pythonExe = Resolve-PythonPath
    if ([string]::IsNullOrWhiteSpace($ApiKey)) {
        $ApiKey = "p6t4i9gco8ZGaA3Y1i26"
    }

    Write-Host "Local API baslatiliyor..." -ForegroundColor Cyan
    Start-Process -FilePath $pythonExe -ArgumentList @(
        "serve_inference.py",
        "--api-key", $ApiKey,
        "--model-id", $ModelId,
        "--dataset", $DatasetPath,
        "--host", "127.0.0.1",
        "--port", "$Port"
    ) | Out-Null

    Start-Sleep -Seconds 2
}

$chromeExe = Resolve-ChromePath
$chromeArgs = @()

if ($UseTempProfile) {
    $profileDir = Join-Path $PSScriptRoot ".chrome-extension-profile"
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir | Out-Null
    }
    $chromeArgs += "--user-data-dir=$profileDir"
}

$chromeArgs += "--disable-extensions-except=$extensionFullPath"
$chromeArgs += "--load-extension=$extensionFullPath"
$chromeArgs += $MeetUrl

Write-Host "Chrome uzanti ile aciliyor..." -ForegroundColor Green
Start-Process -FilePath $chromeExe -ArgumentList $chromeArgs
