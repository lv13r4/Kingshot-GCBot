@echo off
if not exist "venv" (
    echo Virtual environment not found. Running setup first...
    call INSTALL_ON_WINDOWS.bat
)

echo Starting KS Bot...
venv\Scripts\python ksapp.py
pause
