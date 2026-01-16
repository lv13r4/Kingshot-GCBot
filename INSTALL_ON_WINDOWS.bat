@echo off
echo ===========================================
echo    KS Bot Auto-Setup (Windows)
echo ===========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed! 
    echo.
    echo Opening the official Python download page for you...
    start https://www.python.org/downloads/
    echo.
    echo PLEASE: 
    echo 1. Download and run the Python installer.
    echo 2. IMPORTANT: Check the box "Add Python to PATH" during installation!
    echo 3. After installation, run this script again.
    echo.
    pause
    exit /b
)

echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Installing requirements...
venv\Scripts\pip install -r requirements.txt

echo [3/3] Installing browser engine...
venv\Scripts\playwright install chromium

echo.
echo ===========================================
echo    Setup Complete! 
echo    Now you can use 'RUN_ON_WINDOWS.bat'
echo ===========================================
pause
