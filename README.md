# KingShot Gift Code Automation Bot

A fully automated tool to discover and redeem gift codes for the game KingShot. Supports Windows, Linux, and Raspberry Pi.

## Features
- **Auto-Scraper:** Automatically monitors gift code websites for new drops.
- **Discord Monitor:** Listens to Discord channels for codes shared by players.
- **Auto-Redeem:** Automatically logs into the game portal and redeems codes for everyone in your list.
- **Cross-Platform:** Runs on Windows (GUI), Linux, and Raspberry Pi (Headless support).

## Setup Instructions

### Windows
1. Download this repository.
2. Double-click `setup.bat` to install requirements.
3. Fill in your details in `config.json`.
4. Run `python ksapp.py`.

### Linux / Raspberry Pi
1. Download this repository.
2. Run `chmod +x setup_pi.sh && ./setup_pi.sh`.
3. Fill in `config.json`.
4. Run `python3 ksapp.py`.
   - *Note: Use `python3 ksapp.py --headless` to run without a monitor via SSH.*

## Configuration
Edit `config.json` with your own credentials:
- `DISCORD_WEBHOOK`: Where the bot sends notifications.
- `MONITOR_TOKEN`: Your Discord Bot Token for monitoring chat.
- `MONITOR_CHANNEL_ID`: The ID of the channel to watch.

## Disclaimer
This tool is for educational purposes only. Use it at your own risk.
