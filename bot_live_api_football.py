import csv
import requests
import time
from datetime import datetime
import pytz
import os

# === CONFIG ===
API_FOOTBALL_KEY = "f0202fabc0303df003bcca604276ce65"
BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"
NOTIFIED_FILE = "notified_live.txt"
MATCH_FILE = "matches.csv"
MIN_PROBABILITY = 30
MIN_ODDS = 1.4

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Errore Telegram:", e)

def load_notified_ids():
    if not os.path.exists(NOTIFIED_FILE):
        return set()
    with open(NOTIFIED_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_notified_id(mid):
    with open(NOTIFIED_FILE, "a") as f:
        f.write(mid + "\n")

def get_live_events_api_football():
    url = "https://v3.football.api-sports.io/fixtures?live=all"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    try:
        res = requests.get(url, headers=headers)
        return res.json().get("response", [])
    except Exception as e:
        print("Errore API-Football:", e)
        return []

def main():
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    notified_ids = load_notified_ids()
    try:
        with open(MATCH_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            matches = list(reader)
    except FileNotFoundError:
        print("❌ File matches.csv non trovato.")
        return

    live_events = get_live_events_api_football()
    if not live_events:
        print("⚠️ Nessun evento live disponibile.")
        return

    for match in matches:
        try:
            home = match["Home"]
            away = match["Away"]
            prob = int(match["HT Over 0.5 %"])
            if prob < MIN_PROBABILITY:
                continue

            for event in live_events:
                teams = event["teams"]
                if home.lower() in teams["home"]["name"].lower() and away.lower() in teams["away"]["name"].lower():
                    fixture_id = str(event["fixture"]["id"])
                    if fixture_id in notified_ids:
                        continue
                    score = event["goals"]
                    minute = event["fixture"]["status"]["elapsed"]
                    odds_data = event.get("odds", {}).get("1st Half", {}).get("Over 0.5", {})
                    if score["home"] == 0 and score["away"] == 0 and minute >= 1:
                        if odds_data and float(odds_data.get("value", 0)) >= MIN_ODDS:
                            message = f"⚠️ *PARTITA DA MONITORARE LIVE*\n{teams['home']['name']} vs {teams['away']['name']}\n⏱ Minuto: {minute}\n🔥 Over 0.5 HT: *{prob}%*\n*Quota live:* {odds_data['value']}"
                            send_telegram(message)
                            save_notified_id(fixture_id)
        except Exception as e:
            print("Errore elaborazione match:", e)

if __name__ == "__main__":
    main()
