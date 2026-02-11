# Quick Start Backend - Run this in a dedicated terminal
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  CivicLens Backend Server" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

Set-Location "D:\civiclens-frontend\backend"

Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& "D:\civiclens-frontend\backend\venv\Scripts\Activate.ps1"

Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press CTRL+C to stop the server`n" -ForegroundColor Yellow

& "D:\civiclens-frontend\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
