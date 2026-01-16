@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo Installing browser...
playwright install chromium
echo Setup complete!
pause
