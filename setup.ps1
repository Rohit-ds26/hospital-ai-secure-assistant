param(
    [switch]$ResetDb,
    [switch]$StartServer,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Find-Python {
    $candidates = @("py", "python")
    foreach ($candidate in $candidates) {
        try {
            if ($candidate -eq "py") {
                & py -3 --version *> $null
                if ($LASTEXITCODE -eq 0) { return @("py", "-3") }
            } else {
                & python --version *> $null
                if ($LASTEXITCODE -eq 0) { return @("python") }
            }
        } catch {
            continue
        }
    }
    throw "Python 3 was not found. Install Python 3.11+ and rerun this script."
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Step "Preparing Hospital AI System"
$PythonCmd = Find-Python

if (-not (Test-Path ".venv")) {
    Write-Step "Creating virtual environment"
    if ($PythonCmd.Length -gt 1) {
        & $PythonCmd[0] $PythonCmd[1] -m venv .venv
    } else {
        & $PythonCmd[0] -m venv .venv
    }
} else {
    Write-Step "Virtual environment already exists; skipping creation"
}

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python was not found at $VenvPython"
}

Write-Step "Upgrading pip"
& $VenvPython -m pip install --upgrade pip

Write-Step "Installing Python dependencies"
& $VenvPython -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Step "Creating default .env for local mock mode"
    @"
HOSPITAL_AI_PROVIDER=mock
JWT_SECRET=hospital-dev-secret
REPORT_GENERATION_DELAY_SECONDS=0
"@ | Set-Content -Encoding UTF8 ".env"
} else {
    Write-Step ".env already exists; skipping creation"
}

if ($ResetDb -or -not (Test-Path "hospital.db")) {
    Write-Step "Generating demo SQLite database"
    & $VenvPython generate_hospital_data.py
} else {
    Write-Step "hospital.db already exists; skipping database generation"
    Write-Host "    Use .\setup.ps1 -ResetDb to recreate demo data."
}

if (-not (Test-Path "secure_vault")) {
    Write-Step "Creating secure_vault directory"
    New-Item -ItemType Directory -Path "secure_vault" | Out-Null
}

Write-Step "Setup complete"
Write-Host "Run locally with:"
Write-Host "    .\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port $Port"
Write-Host ""
Write-Host "Open:"
Write-Host "    http://127.0.0.1:$Port/"
Write-Host "    http://127.0.0.1:$Port/docs"

if ($StartServer) {
    Write-Step "Starting FastAPI server"
    & $VenvPython -m uvicorn app:app --host 127.0.0.1 --port $Port
}
