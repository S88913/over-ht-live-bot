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
        print("Errore richiesta eventi live:", e)
        return []

def get_live_odds(event_id):
    url = f"https://api.b365api.com/v3/event/view?event_id={event_id}&token={BETSAPI_KEY}"
    try:
        res = requests.get(url)
        data = res.json().get("results", [{}])[0]
        markets = data.get("odds", {}).get("1st Half", [])
        for market in markets:
            if market.get("name") == "Over/Under":
                for o in market.get("odds", []):
                    if o.get("handicap") == "0.5" and o.get("label") == "Over":
                        return float(o.get("value", 0))
        return None
    except Exception as e:
        print("Errore richiesta quota:", e)
        return None

def main():
    notified_ids = load_notified_ids()

    try:
        with open(MATCH_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            matches = [row for row in reader if row.get("Home") and row.get("Away")]
    except Exception as e:
        print("Errore lettura CSV:", e)
        return

    live_events = get_live_events()
    print(f"Eventi live trovati: {len(live_events)}")

    for event in live_events:
        home = event.get("home", "").strip().lower()
        away = event.get("away", "").strip().lower()
        event_id = event.get("id")

        for match in matches:
            match_home = match.get("Home", "").strip().lower()
            match_away = match.get("Away", "").strip().lower()
            over05 = float(match.get("HT Over 0.5", "0"))

            if home == match_home and away == match_away:
                if over05 >= 60 and event.get("ss") == "0-0":
                    time_elapsed = int(event.get("timer", {}).get("tm", 0))
                    odds = get_live_odds(event_id)
                    print(f"Controllo: {home} vs {away} | Tempo: {time_elapsed} | Quota: {odds}")

                    if odds and odds >= 1.40 and event_id not in notified_ids:
                        message = (
                            f"⚠️ *PARTITA DA MONITORARE LIVE*
"
                            f"{home.title()} vs {away.title()}
"
                            f"🕒 Minuto: {time_elapsed}
"
                            f"🔥 Over 0.5 HT: {over05}%
"
                            f"💸 Quota Live: {odds}"
                        )
                        send_telegram(message)
                        save_notified_id(event_id)
    print("✅ FINE CONTROLLO")

if __name__ == "__main__":
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    main()
