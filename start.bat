@echo off
echo ========================================
echo   College Kiosk Enterprise System
echo   Quick Start Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version

echo.
echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists!
)

echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/5] Installing dependencies...
echo This may take a few minutes...
pip install --upgrade pip
pip install Flask Flask-CORS SQLAlchemy pandas numpy requests python-dateutil

echo.
echo [5/5] Starting the application...
echo.
echo ========================================
echo   Application Starting...
echo   Access URL: http://localhost:5000
echo   Admin Panel: http://localhost:5000/admin.html
echo   API Docs: http://localhost:5000/docs/
echo ========================================
echo.

cd backend
python app.py

pause