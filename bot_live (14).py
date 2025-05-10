import csv
import requests
import time
from datetime import datetime
import pytz
import os

# === CONFIG ===
BETSAPI_KEY = "dbc60aec3b60b57175815ab6f1477348"
API_FOOTBALL_KEY = "f0202fabc0303df003bcca604276ce65"
BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"
NOTIFIED_FILE = "notified_live.txt"
MATCH_FILE = "matches.csv"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        print("✅ Inviato:", r.json())
    except Exception as e:
        print("❌ Errore Telegram:", e)

def load_notified_ids():
    if not os.path.exists(NOTIFIED_FILE):
        return set()
    with open(NOTIFIED_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_notified_id(mid):
    with open(NOTIFIED_FILE, "a") as f:
        f.write(mid + "\n")

def get_live_events():
    url = f"https://api.b365api.com/v3/events/inplay?sport_id=1&token={BETSAPI_KEY}"
    try:
        res = requests.get(url)
        return res.json().get("results", [])
    except:
        return []

def get_current_minute(event_time):
    try:
        parts = event_time.split(":")
        return int(parts[0])
    except:
        return -1

def read_match_file():
    matches = []
    try:
        with open(MATCH_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                matches.append(row)
    except Exception as e:
        print("Errore lettura file CSV:", e)
    return matches

def main_loop():
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    notified_ids = load_notified_ids()
    matches = read_match_file()
    live_events = get_live_events()

    for match in matches:
        try:
            home_team = match["Home"].strip().lower()
            away_team = match["Away"].strip().lower()
            match_id = match["id"]
            prob = int(match["HTOver05Prob"])
            if prob < 30:  # soglia modificabile
                continue

            for event in live_events:
                home = event["home"]["name"].strip().lower()
                away = event["away"]["name"].strip().lower()

                if home_team in home and away_team in away:
                    score = event["ss"]
                    if score == "0-0":
                        time_str = event.get("time", {}).get("tm", "0")
                        minute = int(time_str) if time_str else 0
                        odds = event.get("odds", {}).get("1_2", {}).get("1", "0")
                        try:
                            quota = float(odds)
                        except:
                            quota = 0.0
                        if quota >= 1.4 and match_id not in notified_ids:
                            message = (
                                f"⚠️ *PARTITA DA MONITORARE LIVE*\n"
                                f"{event['league']['name']}\n"
                                f"{event['home']['name']} vs {event['away']['name']}\n"
                                f"🕒 Minuto: {minute}\n"
                                f"🔥 Over 0.5 HT: *{prob}%*\n"
                                f"💸 Quota live: {quota}"
                            )
                            send_telegram(message)
                            save_notified_id(match_id)
        except Exception as e:
            print("Errore elaborazione match:", e)

if __name__ == "__main__":
    while True:
        main_loop()
        time.sleep(60)
