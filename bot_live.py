
import csv
import requests
import time
from datetime import datetime
import pytz
import os

# === CONFIG ===
BETSAPI_KEY = "Me4itoG4ZYLWQ3"
BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"
NOTIFIED_FILE = "notified_live.txt"
MATCH_FILE = "matches.csv"
API_FOOTBALL_KEY = "f0202fabc0303df003bcca604276ce65"

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

def get_live_events():
    url = f"https://api.b365api.com/v3/events/inplay?sport_id=1&token={BETSAPI_KEY}"
    try:
        res = requests.get(url)
        return res.json().get("results", [])
    except Exception as e:
        print("Errore API BetsAPI:", e)
        return []

def read_matches():
    matches = []
    with open(MATCH_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                match = {
                    "home": row["Home Team"].strip().lower(),
                    "away": row["Away Team"].strip().lower(),
                    "percent": int(row["FHG Over 0.5%"].replace('%','').strip())
                }
                matches.append(match)
            except Exception as e:
                print("Errore elaborazione match:", e)
    return matches

def main_loop():
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    notified = load_notified_ids()
    matches = read_matches()
    live_matches = get_live_events()

    for event in live_matches:
        home = event.get("home", "").strip().lower()
        away = event.get("away", "").strip().lower()
        score = event.get("ss", "0-0").split("-")
        minute = int(event.get("timer", "0") or "0")
        odds = event.get("odds", {}).get("1st_half", {}).get("over_0.5", {}).get("od", "0")

        for match in matches:
            if match["home"] in home and match["away"] in away:
                if match["percent"] >= 60 and float(odds) >= 1.4 and score == ["0", "0"]:
                    match_id = f"{home}_{away}"
                    if match_id not in notified:
                        message = (
                            f"⚠️ *PARTITA DA MONITORARE LIVE*
"
                            f"{home.title()} vs {away.title()}
"
                            f"🕒 Minuto: {minute}
"
                            f"🔥 Over 0.5 HT: *{match['percent']}%*
"
                            f"💸 Quota live: *{odds}*"
                        )
                        send_telegram(message)
                        save_notified_id(match_id)
                        print(f"Notifica inviata per: {match_id}")
    print("✅ FINE CICLO ESECUZIONE")

if __name__ == "__main__":
    main_loop()
