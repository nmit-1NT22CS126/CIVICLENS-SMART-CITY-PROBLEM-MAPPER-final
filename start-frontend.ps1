# CivicLens Frontend Startup Script
Write-Host "Starting CivicLens Frontend..." -ForegroundColor Cyan

# Navigate to frontend directory
Set-Location "D:\civiclens-frontend"

# Start the development server
Write-Host "Starting Vite dev server..." -ForegroundColor Green
npm run dev
