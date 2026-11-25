$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"

Write-Host "Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Cyan
npm run dev
