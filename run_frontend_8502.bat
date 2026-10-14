@echo off
title Insect Breeding Simulation - Web Dashboard (Port 8502)
echo ======================================================================
echo   Launching Insect Breeding Web Dashboard on http://localhost:8502/
echo   Connecting to FastAPI Backend on http://localhost:8000
echo ======================================================================
cd /d "%~dp0"
start http://localhost:8502/
"C:\Users\bruno\.local\bin\python3.11.exe" -m http.server 8502 --directory frontend
pause
