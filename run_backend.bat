@echo off
title ResumeTailor - Backend Server
cd /d "%~dp0backend"
set "PYTHONPATH=."

:: Check for direct Python binary or standard python
if exist "C:\Users\sunny\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
    echo Starting FastAPI Backend on http://localhost:8000 ...
    "C:\Users\sunny\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo Starting FastAPI Backend on http://localhost:8000 ...
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)
pause
