# Test Backend Connection Script
Write-Host "Testing CivicLens Backend Connection..." -ForegroundColor Cyan

# Test health endpoint
Write-Host "`n1. Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -UseBasicParsing
    Write-Host "Success: Health check successful: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "Error: Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test root endpoint
Write-Host "`n2. Testing root endpoint..." -ForegroundColor Yellow
try {
    $rootResponse = Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET -UseBasicParsing
    Write-Host "Success: Root endpoint successful: $($rootResponse.message)" -ForegroundColor Green
} catch {
    Write-Host "Error: Root endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test auth/login endpoint (should return 422 for missing credentials)
Write-Host "`n3. Testing auth/login endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        email = "test@example.com"
        password = "test123"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    Write-Host "Success: Login endpoint is accessible" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 403 -or $_.Exception.Response.StatusCode -eq 422) {
        Write-Host "Success: Login endpoint is accessible (returned expected error for invalid credentials)" -ForegroundColor Green
    } else {
        Write-Host "Error: Login endpoint error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nSuccess: Backend is running and accessible!" -ForegroundColor Green
Write-Host "Backend URL: http://localhost:8000" -ForegroundColor Cyan
