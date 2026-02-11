# Fix Connection Issues - Complete Reset
Write-Host "Fixing CivicLens Connection Issues..." -ForegroundColor Cyan

# Step 1: Kill all processes on port 8000
Write-Host "`n[1/4] Killing all processes on port 8000..." -ForegroundColor Yellow
$processes = netstat -ano | findstr ":8000" | ForEach-Object {
    if ($_ -match '\s+(\d+)$') {
        $matches[1]
    }
} | Select-Object -Unique

foreach ($pid in $processes) {
    try {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "  Killed process $pid" -ForegroundColor Gray
    } catch {
        # Process already terminated
    }
}
Write-Host "  [OK] Port 8000 cleared" -ForegroundColor Green

# Step 2: Wait a moment
Start-Sleep -Seconds 2

# Step 3: Verify port is free
Write-Host "`n[2/4] Verifying port 8000 is free..." -ForegroundColor Yellow
$stillUsed = netstat -ano | findstr ":8000"
if ($stillUsed) {
    Write-Host "  [WARN] Port still in use, waiting..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
} else {
    Write-Host "  [OK] Port 8000 is free" -ForegroundColor Green
}

# Step 4: Start backend
Write-Host "`n[3/4] Starting backend server..." -ForegroundColor Yellow
Write-Host "  Opening new terminal window for backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", "D:\civiclens-frontend\START_BACKEND.ps1"
Start-Sleep -Seconds 5

# Step 5: Test connection
Write-Host "`n[4/4] Testing connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -UseBasicParsing -TimeoutSec 3
    if ($response.status -eq "healthy") {
        Write-Host "  [OK] Backend is running!" -ForegroundColor Green
        Write-Host "`nSuccess! You can now try logging in." -ForegroundColor Green
        Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  [ERROR] Backend is not responding" -ForegroundColor Red
    Write-Host "  Please check the backend terminal window" -ForegroundColor Yellow
}

Write-Host "`n"
