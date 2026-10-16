@echo off
echo ==============================================
echo   PetFinder (docXaOs) - Startup Script
echo ==============================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Python is not installed or not in PATH.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo Checking and installing dependencies...
pip install -r requirements.txt

if not exist .env (
    if exist .env.example (
        echo Generating .env from template...
        copy .env.example .env
    )
)

echo Starting PetFinder application...
python run.py %*

pause
