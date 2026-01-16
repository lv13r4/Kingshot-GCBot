@echo off
if not exist "venv" (
    echo Virtual environment not found. Running setup first...
    call setup.bat
)

echo Starting KS Bot...
venv\Scripts\python ksapp.py
pause
