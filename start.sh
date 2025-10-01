#!/bin/bash

echo "========================================"
echo "  College Kiosk Enterprise System"
echo "  Quick Start Script"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "[1/5] Checking Python installation..."
python3 --version

echo
echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created successfully!"
else
    echo "Virtual environment already exists!"
fi

echo
echo "[3/5] Activating virtual environment..."
source venv/bin/activate

echo
echo "[4/5] Installing dependencies..."
echo "This may take a few minutes..."
pip install --upgrade pip
pip install Flask Flask-CORS SQLAlchemy pandas numpy requests python-dateutil

echo
echo "[5/5] Starting the application..."
echo
echo "========================================"
echo "  Application Starting..."
echo "  Access URL: http://localhost:5000"
echo "  Admin Panel: http://localhost:5000/admin.html"
echo "  API Docs: http://localhost:5000/docs/"
echo "========================================"
echo

cd backend
python app.py