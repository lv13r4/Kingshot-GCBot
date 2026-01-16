#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import requests
from bs4 import BeautifulSoup
import subprocess
import threading
import time
import os
import sys
from datetime import datetime
import queue
import csv
import re
import json
import argparse

# -----------------------------
# ARGUMENT PARSING
# -----------------------------
parser = argparse.ArgumentParser(description="KS Gift Code Manager (Standalone)")
parser.add_argument("--headless", action="store_true", help="Run without GUI")
args = parser.parse_args()

# -----------------------------
# PATHS & CONFIGURATION
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    default_config = {
        "CHECK_INTERVAL": 3600,
        "TARGET_URL": "https://kingshot.net/gift-codes"
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                user_config = json.load(f)
                return {**default_config, **user_config}
            except:
                return default_config
    return default_config

config = load_config()

CHECK_INTERVAL = config["CHECK_INTERVAL"]
TARGET_URL = config["TARGET_URL"]

REDEEM_SCRIPT = os.path.join(BASE_DIR, "redeemer.py")
CODES_FILE = os.path.join(BASE_DIR, "ks_codes.txt")
LOG_FILE = os.path.join(BASE_DIR, "ks_bot.log")
PLAYERS_CSV = os.path.join(BASE_DIR, "KSGC.csv")
RESULTS_CSV = os.path.join(BASE_DIR, "results.csv")
PYTHON_EXE = sys.executable

# -----------------------------
# THREAD-SAFE LOGGING
# -----------------------------
log_queue = queue.Queue()

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line, end="")
    log_queue.put(line)
    with open(LOG_FILE, "a") as f:
        f.write(line)

def process_log_queue():
    while not log_queue.empty():
        line = log_queue.get()
        if not args.headless:
            terminal_box.insert(tk.END, line)
            terminal_box.see(tk.END)
    if not args.headless:
        root.after(100, process_log_queue)

# -----------------------------
# SHORTCUT CREATION
# -----------------------------
def create_desktop_shortcut():
    try:
        if sys.platform == "win32":
            shortcut_path = os.path.join(os.path.expanduser("~"), "Desktop", "KS Gift Code Bot.lnk")
            target = os.path.join(BASE_DIR, "run.bat")
            icon = sys.executable # Use Python icon
            
            powershell_cmd = (
                f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path}');" 
                f"$s.TargetPath='{target}';" 
                f"$s.WorkingDirectory='{BASE_DIR}';" 
                f"$s.Save()"
            )
            subprocess.run(["powershell", "-Command", powershell_cmd], check=True)
            
        else: # Linux
            desktop_path = os.path.expanduser("~/Desktop/ksbot.desktop")
            run_script = os.path.join(BASE_DIR, "run.sh")
            
            content = f"[Desktop Entry]\nName=KS Gift Code Bot\nExec={run_script}\nIcon=utilities-terminal\nType=Application\nTerminal=false\nCategories=Utility;\n"
            with open(desktop_path, "w") as f:
                f.write(content)
            os.chmod(desktop_path, 0o755)

        log("🚀 Desktop shortcut created!")
        if not args.headless:
            messagebox.showinfo("Success", "Desktop shortcut created successfully!")
    except Exception as e:
        log(f"❌ Failed to create shortcut: {e}")
        if not args.headless:
            messagebox.showerror("Error", f"Could not create shortcut: {e}")

# -----------------------------
# HISTORY MANAGEMENT
# -----------------------------
def clear_history():
    if not args.headless:
        if not messagebox.askyesno("Confirm", "This will clear all discovered codes and redemption results. The bot will try to redeem all active codes again. Continue?"):
            return

    try:
        if os.path.exists(CODES_FILE): os.remove(CODES_FILE)
        if os.path.exists(RESULTS_CSV): os.remove(RESULTS_CSV)
        log("🗑️ History cleared (Codes and Results).")
        if not args.headless:
            messagebox.showinfo("Success", "Redemption history has been cleared.")
    except Exception as e:
        log(f"❌ Error clearing history: {e}")
        if not args.headless:
            messagebox.showerror("Error", f"Failed to clear history: {e}")

# -----------------------------
# PLAYER MANAGEMENT (CSV)
# -----------------------------
def add_player_to_csv(player_id):
    player_id = player_id.strip()
    if not player_id:
        if not args.headless: messagebox.showwarning("Warning", "Please enter a Player ID.")
        return False
    
    try:
        existing_ids = []
        if os.path.exists(PLAYERS_CSV):
            with open(PLAYERS_CSV, 'r', newline='') as f:
                reader = csv.reader(f)
                existing_ids = [row[0] for row in reader if row]

        if player_id in existing_ids:
            log(f"⚠️ Duplicate: Player ID {player_id} already exists.")
            if not args.headless: messagebox.showinfo("Info", f"Player ID {player_id} already in list.")
            return False

        with open(PLAYERS_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([player_id])
            
        log(f"✅ Added Player ID: {player_id}")
        if not args.headless: 
            player_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Player {player_id} added successfully.")
        return True

    except Exception as e:
        log(f"❌ CSV Error: {e}")
        if not args.headless: messagebox.showerror("Error", f"Failed to save player: {e}")
        return False

# -----------------------------
# CODE STORAGE & SCRAPER
# -----------------------------
def load_sent_codes():
    if not os.path.exists(CODES_FILE): return set()
    with open(CODES_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_sent_code(code):
    mode = 'a+' if os.path.exists(CODES_FILE) and os.path.getsize(CODES_FILE) > 0 else 'a'
    with open(CODES_FILE, mode) as f:
        if mode == 'a+':
            f.seek(f.tell() - 1, os.SEEK_SET)
            if f.read(1) != '\n': f.write('\n')
        f.write(code + "\n")

def scrape_codes():
    try:
        r = requests.get(TARGET_URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text_lines = soup.get_text(separator="\n").split("\n")
        codes = []
        in_active = False
        for line in text_lines:
            line = line.strip()
            if line.lower() == "active gift codes": in_active = True; continue
            if line.lower() == "expired gift codes": in_active = False
            if in_active and line.isalnum() and 4 <= len(line) <= 20 and line.lower() != "active":
                codes.append(line)
        return list(dict.fromkeys(codes))
    except Exception as e:
        log(f"Scrape error: {e}")
        return []

# -----------------------------
# BOT LOGIC
# -----------------------------
def update_status(text):
    if not args.headless:
        root.after(0, lambda: status_label.config(text=f"Status: {text}"))

def check_new_codes():
    update_status("Checking...")
    sent_codes = load_sent_codes()
    scraped_codes = scrape_codes()
    added_codes = []
    for code in scraped_codes:
        if code not in sent_codes:
            save_sent_code(code)
            sent_codes.add(code)
            added_codes.append(code)
            log(f"New code found: {code}")
    if added_codes:
        log("New codes detected, starting redeemer automatically.")
        threading.Thread(target=run_redeemer, args=(added_codes,), daemon=True).start()
    else:
        log("No new codes found.")
    if not args.headless:
        root.after(0, lambda: last_check_label.config(text=f"Last Check: {datetime.now().strftime('%H:%M:%S')}"))
    update_status("Idle")
    return added_codes

redeemer_lock = threading.Lock()
def run_redeemer(new_codes=None):
    if not redeemer_lock.acquire(blocking=False):
        log("Redeemer is already running.")
        return False
    try:
        update_status("Redeeming...")
        log("Running redeemer...")
        command = [PYTHON_EXE, REDEEM_SCRIPT, ""] 
        if new_codes: command.extend(new_codes)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: log(line.strip())
        proc.wait()
        if not args.headless:
            root.after(0, lambda: last_redeem_label.config(text=f"Last Redeem: {datetime.now().strftime('%H:%M:%S')}"))
        return True
    except Exception as e: log(f"Redeemer error: {e}"); return False
    finally:
        update_status("Idle")
        redeemer_lock.release()

running = False
def start_auto_check():
    global running
    if not running:
        running = True
        threading.Thread(target=auto_check_loop, daemon=True).start()
        log("Auto-check started.")

def auto_check_loop():
    while running:
        check_new_codes()
        for _ in range(int(CHECK_INTERVAL)):
            if not running: break
            time.sleep(1)

# -----------------------------
# GUI
# -----------------------------
if args.headless:
    log("Running in STANDALONE HEADLESS mode.")
    start_auto_check()
    try:
        while True: time.sleep(1); process_log_queue()
    except KeyboardInterrupt: log("Stopping bot..."); running = False
else:
    root = tk.Tk()
    root.title("KS Gift Code Manager")
    root.geometry("600x600")

    status_frame = tk.LabelFrame(root, text="Status Information", padx=10, pady=5)
    status_frame.pack(fill="x", padx=10, pady=5)
    status_label = tk.Label(status_frame, text="Status: Idle", anchor="w")
    status_label.pack(fill="x")
    last_check_label = tk.Label(status_frame, text="Last Check: Never", anchor="w")
    last_check_label.pack(fill="x")
    last_redeem_label = tk.Label(status_frame, text="Last Redeem: Never", anchor="w")
    last_redeem_label.pack(fill="x")

    player_frame = tk.LabelFrame(root, text="Add New Player", padx=10, pady=5)
    player_frame.pack(fill="x", padx=10, pady=5)
    tk.Label(player_frame, text="Player ID:").pack(side="left")
    player_entry = tk.Entry(player_frame, width=20)
    player_entry.pack(side="left", padx=5)
    tk.Button(player_frame, text="Add Player", command=lambda: add_player_to_csv(player_entry.get())).pack(side="left", padx=5)

    button_frame = tk.Frame(root)
    button_frame.pack(padx=10, pady=5)
    tk.Button(button_frame, text="Check for New Codes", width=20,
              command=lambda: threading.Thread(target=check_new_codes, daemon=True).start()).grid(row=0, column=0, padx=5, pady=5)
    tk.Button(button_frame, text="Redeem Codes Now", width=20,
              command=lambda: threading.Thread(target=run_redeemer, daemon=True).start()).grid(row=0, column=1, padx=5, pady=5)

    # Shortcut & History
    util_frame = tk.Frame(root)
    util_frame.pack(fill="x", padx=10, pady=5)
    tk.Button(util_frame, text="Create Desktop Shortcut", bg="#4CAF50", fg="white", 
              command=create_desktop_shortcut).pack(side="left", fill="x", expand=True, padx=2)
    tk.Button(util_frame, text="Clear History", bg="#ff4d4d", fg="white",
              command=clear_history).pack(side="left", fill="x", expand=True, padx=2)

    terminal_box = ScrolledText(root, height=12, bg="black", fg="lime", insertbackground="lime")
    terminal_box.pack(fill="both", expand=True, padx=10, pady=5)
    terminal_box.insert(tk.END, "=== KS Bot Log ===\n")

    def on_close(): global running; running = False; root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
    process_log_queue()
    start_auto_check()
    root.mainloop()
