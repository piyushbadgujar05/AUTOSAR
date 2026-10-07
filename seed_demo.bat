@echo off
title Seed Demo HLD Data
echo ================================================================
echo  Generating Synthetic HLD PDFs & Seeding Knowledge Base
echo ================================================================

cd /d "%~dp0"

set PYTHONPATH=.
set USE_FAST_EMBEDDINGS=1

echo 1. Generating synthetic automotive HLD documents...
.\.venv\Scripts\python.exe scripts\generate_sample_pdfs.py

echo 2. Indexing documents into ChromaDB & extracting architecture...
.\.venv\Scripts\python.exe scripts\seed_demo_data.py

echo.
echo Demo data seeded successfully!
pause
