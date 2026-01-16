#!/bin/bash
echo "--- Raspberry Pi Setup for KS Bot ---"

# Update system
sudo apt update

# Install Tkinter (for the GUI) and other system dependencies
sudo apt install -y python3-tk python3-pip libnss3 libnspr4 libgbm1 libasound2

# Install Python requirements
pip3 install -r requirements.txt

# Install Playwright and its browser dependencies
pip3 install playwright
playwright install-deps
playwright install chromium

echo "--- Setup Complete ---"
echo "To start the bot, run: python3 ksapp.py"
