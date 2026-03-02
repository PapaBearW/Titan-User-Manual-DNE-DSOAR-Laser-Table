@echo off
title Titan Laser Manual Query

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please download it from https://www.python.org/downloads/
    pause
    exit /b
)

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Setting up for the first time - this takes about 1 minute...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install --quiet -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: Launch the app
echo Opening Titan Laser Manual Query in your browser...
streamlit run query_app.py

pause
