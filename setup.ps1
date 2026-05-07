# setup.ps1 — Windows PowerShell setup script

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Agent System - Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python version - require 3.10+
$version = python --version 2>&1
$versionNumber = ($version -replace "Python ", "").Trim()
$parts = $versionNumber.Split(".")
$major = [int]$parts[0]
$minor = [int]$parts[1]

Write-Host "-> Found: Python $versionNumber" -ForegroundColor Green

if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Host "ERROR: Python 3.10 or higher is required." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "-> Version check passed (3.10+)" -ForegroundColor Green

# Create venv
if (-Not (Test-Path ".venv")) {
    Write-Host "-> Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "-> .venv already exists, skipping" -ForegroundColor DarkGray
}

# Activate
Write-Host "-> Activating venv..." -ForegroundColor Yellow
.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip --quiet

# Install deps
Write-Host "-> Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Copy .env
if (-Not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "-> Created .env - add your API keys now" -ForegroundColor Green
} else {
    Write-Host "-> .env already exists, skipping" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "  Activate : .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  Run      : python main.py" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan