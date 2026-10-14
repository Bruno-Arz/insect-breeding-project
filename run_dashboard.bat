@echo off
title Insect Selective Breeding Simulator - Streamlit Dashboard
echo ======================================================================
echo   Launching Insect Selective Breeding Simulator Dashboard...
echo ======================================================================
cd /d "%~dp0"
"C:\Users\bruno\.local\bin\python3.11.exe" -m streamlit run app.py
pause
