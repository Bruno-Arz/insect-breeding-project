@echo off
title Insect Breeding Simulation - Backend API (FastAPI)
echo ======================================================================
echo   Starting Insect Selective Breeding FastAPI Backend Server...
echo   Listening on http://127.0.0.1:8000 (CORS Enabled for Bolt.ai)
echo ======================================================================
cd /d "%~dp0"
"C:\Users\bruno\.local\bin\python3.11.exe" -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
pause
