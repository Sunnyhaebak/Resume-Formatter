$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\backend"
$env:PYTHONPATH = "."

$pythonBin = "C:\Users\sunny\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $pythonBin)) {
    $pythonBin = "python"
}

Write-Host "Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Cyan
& $pythonBin -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
