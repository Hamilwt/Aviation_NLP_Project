@echo off
cd /d "C:\vs code\NLP-Aviation-Safety\Aviation_NLP_Project\aviation-safety-app\backend"
call venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000