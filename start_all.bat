@echo off
title Insect Selective Breeding System - Master Launcher
echo ======================================================================
echo   Starting Complete Insect Selective Breeding System (30%% Milestone)
echo ======================================================================
cd /d "%~dp0"

echo 1. Starting FastAPI Backend Server on http://127.0.0.1:8000...
start "FastAPI Backend (Port 8000)" cmd /k ""C:\Users\bruno\.local\bin\python3.11.exe" -m uvicorn api:app --host 127.0.0.1 --port 8000"

timeout /t 2 >nul

echo 2. Starting Web Dashboard on http://localhost:8502/...
start http://localhost:8502/
"C:\Users\bruno\.local\bin\python3.11.exe" -m http.server 8502 --directory frontend

pause
