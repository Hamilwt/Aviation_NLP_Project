<# 
.SYNOPSIS
    Safety NLP Pipeline - One-Click Launcher (PowerShell)
#>

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Safety NLP Pipeline - One-Click Launcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if artifacts exist
$artifactsPath = "safety_nlp_pipeline\data\safety_model.pkl"
if (-not (Test-Path $artifactsPath)) {
    Write-Host "[1/3] ML artifacts not found. Running pipeline first..." -ForegroundColor Yellow
    Write-Host "This may take 2-5 minutes on first run..." -ForegroundColor Gray
    Set-Location "safety_nlp_pipeline"
    pip install -r requirements.txt 2>$null | Out-Null
    python main.py
    Set-Location ".."
    Write-Host ""
    Write-Host "Pipeline complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/3] ML artifacts found. Skipping pipeline." -ForegroundColor Green
    Write-Host ""
}

Write-Host "[2/3] Starting Backend API..." -ForegroundColor Yellow

$backendScript = {
    Set-Location "aviation-safety-app\backend"
    if (-not (Test-Path "venv")) {
        python -m venv venv
    }
    & "venv\Scripts\Activate.ps1"
    pip install -r requirements.txt 2>$null | Out-Null
    python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>$null
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
}

Start-Process powershell -WindowStyle Normal -ArgumentList "-NoExit", "-Command", $backendScript.ToString()

Write-Host "Waiting for backend to start..." -ForegroundColor Gray
Start-Sleep -Seconds 12

Write-Host "[3/3] Starting Frontend..." -ForegroundColor Yellow

$frontendScript = {
    Set-Location "aviation-safety-app\frontend"
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run dev
}

Start-Process powershell -WindowStyle Normal -ArgumentList "-NoExit", "-Command", $frontendScript.ToString()

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "First time? Go to System Control page and click 'Load Artifacts'" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"