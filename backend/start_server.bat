@echo off
cd /d D:\civiclens-frontend\backend
"D:\civiclens-frontend\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
