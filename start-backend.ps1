# CivicLens Backend Startup Script
Write-Host "Starting CivicLens Backend..." -ForegroundColor Cyan

# Navigate to backend directory
Set-Location "D:\civiclens-frontend\backend"

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "D:\civiclens-frontend\backend\venv\Scripts\Activate.ps1"

# Start the backend server
Write-Host "Starting uvicorn server..." -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
