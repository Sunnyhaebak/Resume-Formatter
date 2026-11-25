@echo off
title ResumeTailor - Full Stack Launcher
echo ========================================================
echo    Launching ResumeTailor AI Engine (Backend + Frontend)
echo ========================================================

:: 1. Launch Backend in a separate cmd window
echo [1/2] Starting Backend API Server (Port 8000)...
start "ResumeTailor Backend" "%~dp0run_backend.bat"

:: Wait 2 seconds for backend initialization
timeout /t 2 /nobreak > nul

:: 2. Launch Frontend in a separate cmd window
echo [2/2] Starting Next.js Frontend (Port 3000)...
start "ResumeTailor Frontend" "%~dp0run_frontend.bat"

:: Wait 3 seconds then open browser
timeout /t 3 /nobreak > nul
echo Opening http://localhost:3000 in your browser...
start http://localhost:3000

echo.
echo Both servers are now running!
echo - Backend API:  http://localhost:8000 (Docs at /docs)
echo - Frontend PWA: http://localhost:3000
echo.
pause
