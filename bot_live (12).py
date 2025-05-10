
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
    except Exception as e:
        print("Errore API BetsAPI:", e)
        return []

def get_csv_matches():
    matches = []
    try:
        with open(MATCH_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                matches.append(row)
    except Exception as e:
        print("Errore lettura CSV:", e)
    return matches

def main_loop():
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    notified_ids = load_notified_ids()
    matches = get_csv_matches()
    live_events = get_live_events()

    for match in matches:
        try:
            home = match["Home"].strip()
            away = match["Away"].strip()
            team_names = [home.lower(), away.lower()]

            over05_prob = int(match["FHG Over 0.5 %"].replace("%", "").strip())
            if over05_prob < 30:
                continue

            for event in live_events:
                live_home = event["home"]["name"].strip().lower()
                live_away = event["away"]["name"].strip().lower()
                live_odds_data = event.get("odds", {}).get("1_5", {})

                if live_home in team_names and live_away in team_names:
                    event_id = str(event["id"])
                    if event_id in notified_ids:
                        continue

                    match_time = int(event["time"])
                    if match_time < 1 or match_time > 45:
                        continue

                    if "1" in live_odds_data:
                        live_odds = float(live_odds_data["1"])
                        if live_odds < 1.4:
                            continue
                    else:
                        continue

                    message = (
                        f"⚠️ *PARTITA DA MONITORARE LIVE*
"
                        f"{event['league']['name']}
"
                        f"{home} vs {away}
"
                        f"🕒 Minuto: {match_time}’
"
                        f"🔥 Over 0.5 HT: {over05_prob}%
"
                        f"💸 Quota Live: {live_odds}"
                    )
                    send_telegram(message)
                    save_notified_id(event_id)
        except Exception as e:
            print("Errore elaborazione match:", e)

if __name__ == "__main__":
    while True:
        main_loop()
        time.sleep(60)
