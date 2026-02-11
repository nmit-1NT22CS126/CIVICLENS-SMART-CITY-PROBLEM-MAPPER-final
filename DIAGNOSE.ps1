Write-Host "`n========================================"ForegroundColor Cyan
Write-Host "  CivicLens System Diagnostic" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check if backend is running
Write-Host "[1/5] Checking if backend is running..." -ForegroundColor Yellow
$backendRunning = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -UseBasicParsing -TimeoutSec 2
    if ($response.status -eq "healthy") {
        Write-Host "  [OK] Backend is running" -ForegroundColor Green
        $backendRunning = $true
    }
} catch {
    Write-Host "  [ERROR] Backend is NOT running" -ForegroundColor Red
}

# 2. Check port 8000
Write-Host "`n[2/5] Checking port 8000..." -ForegroundColor Yellow
$portUsage = netstat -ano | findstr ":8000"
if ($portUsage) {
    Write-Host "  [OK] Port 8000 is in use" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] No process on port 8000" -ForegroundColor Red
}

# 3. Check frontend
Write-Host "`n[3/5] Checking frontend..." -ForegroundColor Yellow
$frontendRunning = $false
try {
    $null = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
    Write-Host "  [OK] Frontend is running on port 5173" -ForegroundColor Green
    $frontendRunning = $true
} catch {
    Write-Host "  [ERROR] Frontend is NOT running" -ForegroundColor Red
}

# 4. Check Supabase config
Write-Host "`n[4/5] Checking Supabase..." -ForegroundColor Yellow
if (Test-Path "D:\civiclens-frontend\backend\.env") {
    Write-Host "  [OK] .env file exists" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] .env file missing" -ForegroundColor Red
}

# 5. Test login
if ($backendRunning) {
    Write-Host "`n[5/5] Testing login endpoint..." -ForegroundColor Yellow
    try {
        $body = @{ email = "test@test.com"; password = "test123" } | ConvertTo-Json
        $null = Invoke-WebRequest -Uri "http://localhost:8000/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
        Write-Host "  [OK] Login endpoint works" -ForegroundColor Green
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 403) {
            Write-Host "  [OK] Login endpoint accessible" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Login endpoint error" -ForegroundColor Red
        }
    }
}

# Summary
Write-Host "`n========================================"  -ForegroundColor Cyan
if ($backendRunning -and $frontendRunning) {
    Write-Host "System Ready!" -ForegroundColor Green
} else {
    Write-Host "Action Required:" -ForegroundColor Red
    if (-not $backendRunning) { Write-Host "  - Run: .\START_BACKEND.ps1" -ForegroundColor Yellow }
    if (-not $frontendRunning) { Write-Host "  - Run: .\START_FRONTEND.ps1" -ForegroundColor Yellow }
}
Write-Host "`n"
