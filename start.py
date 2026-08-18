#!/usr/bin/env python3
"""
Safety NLP Pipeline - One-Click Launcher (Python)
Run this single file to start everything: python start.py
"""
import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
PIPELINE_DIR = ROOT / "safety_nlp_pipeline"
BACKEND_DIR = ROOT / "aviation-safety-app" / "backend"
FRONTEND_DIR = ROOT / "aviation-safety-app" / "frontend"

processes = []

def run_cmd(cmd, cwd=None, shell=True, background=False):
    """Run command, optionally in background."""
    if background:
        proc = subprocess.Popen(cmd, cwd=cwd, shell=shell)
        processes.append(proc)
        return proc
    else:
        # Ensure command is properly quoted for paths with spaces
        if isinstance(cmd, list):
            cmd = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        return subprocess.run(cmd, cwd=cwd, shell=shell, check=True)

def check_artifacts():
    """Check if ML artifacts exist."""
    return (PIPELINE_DIR / "data" / "safety_model.pkl").exists()

def install_pipeline():
    """Install pipeline dependencies and run."""
    print("[1/4] Installing pipeline dependencies...")
    run_cmd("pip install -r requirements.txt", cwd=PIPELINE_DIR)
    print("[2/4] Running pipeline (first time, 2-5 min)...")
    run_cmd("python main.py", cwd=PIPELINE_DIR)
    print("✓ Pipeline complete!")

def start_backend():
    """Start FastAPI backend."""
    print("[3/4] Starting Backend API...")
    
    # Setup venv
    venv_dir = BACKEND_DIR / "venv"
    if not venv_dir.exists():
        run_cmd("python -m venv venv", cwd=BACKEND_DIR)
    
    # Determine python executable
    if sys.platform == "win32":
        python_exe = str(venv_dir / "Scripts" / "python.exe")
    else:
        python_exe = str(venv_dir / "bin" / "python")
    
    # Install deps using list form to avoid quoting issues
    subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], cwd=BACKEND_DIR, check=True)
    
    # Download NLTK data
    subprocess.run([python_exe, "-c", 
        "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('punkt_tab', quiet=True)"], 
        cwd=BACKEND_DIR, check=True)
    
    # Start uvicorn in background
    uvicorn_cmd = [python_exe, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    if sys.platform == "win32":
        # Windows: use cmd /k to keep window open
        subprocess.Popen(["cmd", "/k"] + uvicorn_cmd, cwd=BACKEND_DIR)
    else:
        # Linux/Mac: background process
        proc = subprocess.Popen(uvicorn_cmd, cwd=BACKEND_DIR)
        processes.append(proc)
    
    print("[OK] Backend starting on http://localhost:8000")

def start_frontend():
    """Start React frontend."""
    print("[4/4] Starting Frontend...")
    
    # Install deps
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  Installing npm packages...")
        run_cmd("npm install", cwd=FRONTEND_DIR)
    
    # Start vite dev server in background
    if sys.platform == "win32":
        subprocess.Popen(
            ["cmd", "/k", "npm run dev"],
            cwd=FRONTEND_DIR
        )
    else:
        proc = subprocess.Popen(
            ["bash", "-c", "npm run dev"],
            cwd=FRONTEND_DIR
        )
        processes.append(proc)
    
    print("[OK] Frontend starting on http://localhost:5173")

def wait_for_backend():
    """Wait for backend to be ready."""
    print("Waiting for backend to start...")
    for _ in range(30):
        try:
            import requests
            r = requests.get("http://localhost:8000/api/health", timeout=2)
            if r.status_code == 200:
                print("✓ Backend ready!")
                return
        except:
            pass
        time.sleep(1)
    print("⚠ Backend may still be starting...")

def main():
    print("=" * 50)
    print("  Safety NLP Pipeline - One-Click Launcher")
    print("=" * 50)
    print()
    
    # Check artifacts
    if not check_artifacts():
        print("ML artifacts not found. Running pipeline first...")
        install_pipeline()
    else:
        print("[OK] ML artifacts found")
    
    # Start services
    start_backend()
    wait_for_backend()
    start_frontend()
    
    print()
    print("=" * 50)
    print("  All services started!")
    print("=" * 50)
    print()
    print("  Frontend:  http://localhost:5173")
    print("  Backend:   http://localhost:8000")
    print("  API Docs:  http://localhost:8000/docs")
    print()
    print("  First time? Go to System Control → click 'Load Artifacts'")
    print()
    print("  Press Ctrl+C to stop all services")
    print()
    
    # Open browser
    try:
        webbrowser.open("http://localhost:5173")
    except:
        pass
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        for p in processes:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()