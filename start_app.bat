@echo off
echo ============================================
echo  Safety NLP Pipeline - One-Click Launcher
echo ============================================
echo.

REM Check if artifacts exist, if not run pipeline first
if not exist "safety_nlp_pipeline\data\safety_model.pkl" (
    echo [1/3] ML artifacts not found. Running pipeline first...
    echo This may take 2-5 minutes on first run...
    cd safety_nlp_pipeline
    pip install -r requirements.txt >nul 2>&1
    python main.py
    cd ..
    echo.
    echo Pipeline complete!
    echo.
) else (
    echo [1/3] ML artifacts found. Skipping pipeline.
    echo.
)

echo [2/3] Starting Backend API...
start "Safety NLP Backend" cmd /k "
cd aviation-safety-app\backend
if not exist venv (
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
) else (
    venv\Scripts\activate
)
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>nul
python -m uvicorn main:app --host 0.0.0.0 --port 8000
"

echo Waiting for backend to start...
timeout /t 10 /nobreak >nul

echo [3/3] Starting Frontend...
start "Safety NLP Frontend" cmd /k "
cd aviation-safety-app\frontend
if not exist node_modules (
    npm install
)
npm run dev
"

echo.
echo ============================================
echo  All services started!
echo ============================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo First time? Go to System Control page and click "Load Artifacts"
echo.
pause