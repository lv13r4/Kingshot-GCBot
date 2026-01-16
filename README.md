# KingShot Gift Code Automation Bot

A standalone tool to automatically discover and redeem gift codes for the game KingShot. No Discord bot setup required!

## Features
- **Auto-Scraper:** Automatically monitors gift code websites for new drops.
- **Easy Player Management:** Add Player IDs directly through the app interface.
- **Auto-Redeem:** Automatically logs into the game portal and redeems codes for everyone in your list.
- **Cross-Platform:** Runs on Windows (GUI), Linux, and Raspberry Pi (Headless support).

## Setup Instructions

### Windows
1. Download this repository.
2. Double-click `setup.bat` to install requirements.
3. Run `python ksapp.py`.
4. Enter your Player ID in the app and click "Add Player."

### Linux / Raspberry Pi
1. Download this repository.
2. Run `chmod +x setup_pi.sh && ./setup_pi.sh`.
3. Run `python3 ksapp.py`.
   - *Note: Use `python3 ksapp.py --headless` to run without a monitor via SSH.*

## Disclaimer
This tool is for educational purposes only. Use it at your own risk.