@echo off
echo ===========================================
echo    KS Bot Auto-Setup (Windows)
echo ===========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed! 
    echo Please install Python from python.org and try again.
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
echo    Now you can use 'run.bat' to start the bot.
echo ===========================================
pause