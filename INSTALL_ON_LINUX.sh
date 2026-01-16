#!/bin/bash
echo "--- Raspberry Pi Setup for KS Bot ---"

# Update system
sudo apt update

# Install Tkinter and venv support
sudo apt install -y python3-tk python3-pip python3-venv libnss3 libnspr4 libgbm1 libasound2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Install Playwright and its browser dependencies
pip3 install playwright
playwright install-deps
playwright install chromium

echo "--- Setup Complete ---"
echo "To start the bot, run: python3 ksapp.py"
