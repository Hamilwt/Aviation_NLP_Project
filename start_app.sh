#!/bin/bash
# Safety NLP Pipeline - One-Click Launcher (Linux/Mac)

set -e

echo "============================================"
echo "  Safety NLP Pipeline - One-Click Launcher"
echo "============================================"
echo

# Check if artifacts exist
if [ ! -f "safety_nlp_pipeline/data/safety_model.pkl" ]; then
    echo "[1/3] ML artifacts not found. Running pipeline first..."
    echo "This may take 2-5 minutes on first run..."
    cd safety_nlp_pipeline
    pip install -r requirements.txt > /dev/null 2>&1
    python main.py
    cd ..
    echo
    echo "Pipeline complete!"
    echo
else
    echo "[1/3] ML artifacts found. Skipping pipeline."
    echo
fi

echo "[2/3] Starting Backend API..."

# Start backend in background
cd aviation-safety-app/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>/dev/null

# Start uvicorn in background
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

echo "Waiting for backend to start..."
sleep 12

echo "[3/3] Starting Frontend..."

# Start frontend in background
cd aviation-safety-app/frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ../..

echo
echo "============================================"
echo "  All services started!"
echo "============================================"
echo
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo
echo "First time? Go to System Control page and click 'Load Artifacts'"
echo
echo "Press Ctrl+C to stop all services"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait