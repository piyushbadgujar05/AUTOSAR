@echo off
title AUTOSAR HLD Document Analysis Assistant
echo ================================================================
echo  Starting AUTOSAR HLD Document Analysis Assistant (No Docker)
echo ================================================================

cd /d "%~dp0"

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo Error: Virtual environment .venv not found.
    echo Please make sure .venv is installed.
    pause
    exit /b 1
)

set PYTHONPATH=.
set USE_FAST_EMBEDDINGS=1

echo Launching Full-Stack Services...
echo  - Backend API:  http://127.0.0.1:8000/docs
echo  - Frontend UI:  http://127.0.0.1:8501
echo ================================================================

.\.venv\Scripts\python.exe run.py

pause
