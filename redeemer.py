import os
import sys
import time
import json
import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import requests
import openpyxl

# -----------------------------
# PATHS
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERS_XLSX = os.path.join(BASE_DIR, 'KSGC.xlsx')
CODES_FILE = os.path.join(BASE_DIR, 'ks_codes.txt')
RESULTS_CSV = os.path.join(BASE_DIR, 'results.csv')
LOCK_FILE = os.path.join(BASE_DIR, 'redeem.lock')

# -----------------------------
# LOCKING
# -----------------------------
def create_lock():
    if os.path.exists(LOCK_FILE):
        print("🔒 Redeemer already running.")
        return False
    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))
    return True

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# -----------------------------
# DATA LOADING
# -----------------------------
def load_players():
    try:
        if not os.path.exists(PLAYERS_XLSX):
            return []
        df = pd.read_excel(PLAYERS_XLSX, header=None)
        return df[0].astype(str).str.strip().tolist()
    except Exception as e:
        print(f"❌ Error loading players: {e}")
        return []

def load_codes():
    if not os.path.exists(CODES_FILE):
        return []
    with open(CODES_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def load_results():
    results = {}
    if not os.path.exists(RESULTS_CSV):
        return results
    try:
        df = pd.read_csv(RESULTS_CSV)
        for _, row in df.iterrows():
            p_id = str(row['PlayerID'])
            code = str(row['GiftCode'])
            status = str(row['Status'])
            if p_id not in results:
                results[p_id] = {}
            results[p_id][code] = status
    except:
        pass
    return results

def save_result_line(player, code, status):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(RESULTS_CSV)
    df = pd.DataFrame([[player, code, status, ts]], columns=['PlayerID', 'GiftCode', 'Status', 'Timestamp'])
    df.to_csv(RESULTS_CSV, mode='a', header=not file_exists, index=False)

def save_codes(codes):
    with open(CODES_FILE, 'w') as f:
        f.write("\n".join(codes) + "\n")

# -----------------------------
# DISCORD
# -----------------------------
def send_discord(webhook, message):
    if not webhook: return
    try:
        requests.post(webhook, json={"content": message}, timeout=10)
    except:
        pass

# -----------------------------
# MAIN REDEEMER
# -----------------------------
async def run_redeemer(webhook, new_codes_from_args=None):
    if not create_lock(): return
    
    try:
        players = load_players()
        if not players:
            print("No players found.")
            return

        codes = load_codes()
        results = load_results()
        previous_results = json.loads(json.dumps(results))
        attempted_codes = set()

        if not codes:
            print("No codes found.")
            return

        async with async_playwright() as p:
            # Launch browser (bundled or system)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            for player_id in players:
                print(f"▶ Processing Player: {player_id}")
                await page.goto('https://ks-giftcode.centurygame.com/', wait_until='networkidle')
                
                tried = results.get(player_id, {})
                pending = [c for c in codes if tried.get(c) not in ['Successful', 'Already claimed']]

                if not pending:
                    print(f"⏩ Skip {player_id} (All codes done)")
                    continue

                try:
                    # Login
                    await page.wait_for_selector('input[placeholder="Player ID"]', timeout=15000)
                    await page.fill('input[placeholder="Player ID"]', player_id)
                    await page.click('.btn.login_btn')
                    await asyncio.sleep(1.5)

                    for code in pending:
                        attempted_codes.add(code)
                        print(f"  Redeeming {code}...")
                        
                        await page.wait_for_selector('input[placeholder="Enter Gift Code"]', timeout=10000)
                        await page.fill('input[placeholder="Enter Gift Code"]', code)
                        await page.click('.btn.exchange_btn')
                        await asyncio.sleep(1.5)

                        status = "Unknown"
                        try:
                            msg = (await page.inner_text('.msg')).lower()
                            if 'redeemed' in msg: status = 'Successful'
                            elif 'already claimed' in msg: status = 'Already claimed'
                            elif 'expired' in msg: status = 'Expired'
                            elif 'not found' in msg: status = 'Invalid'
                            elif 'claim limit' in msg: status = 'Invalid'
                        except:
                            pass

                        # Close popups
                        try:
                            await page.click('.swal2-confirm', timeout=500)
                        except:
                            try: await page.keyboard.press('Escape')
                            except: pass

                        save_result_line(player_id, code, status)
                        if player_id not in results: results[player_id] = {}
                        results[player_id][code] = status

                        if status in ['Expired', 'Invalid']:
                            codes = [c for c in codes if c != code]
                            save_codes(codes)
                        
                        await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"❌ Error for {player_id}: {e}")

            await browser.close()

        # Check for newly completed codes
        newly_completed = []
        for code in attempted_codes:
            is_done = all(results.get(p, {}).get(code) in ['Successful', 'Already claimed'] for p in players)
            if is_done:
                was_done = all(previous_results.get(p, {}).get(code) in ['Successful', 'Already claimed'] for p in players)
                if not was_done:
                    newly_completed.append(code)

        if newly_completed and new_codes_from_args:
            final_notify = [c for c in newly_completed if c in new_codes_from_args]
            if final_notify:
                msg = f"{', '.join(final_notify)} Gift Code(s) redeemed successfully for the list."
                send_discord(webhook, msg)

    finally:
        remove_lock()

if __name__ == "__main__":
    webhook_url = sys.argv[1] if len(sys.argv) > 1 else None
    args_codes = sys.argv[2:] if len(sys.argv) > 2 else []
    asyncio.run(run_redeemer(webhook_url, args_codes))
