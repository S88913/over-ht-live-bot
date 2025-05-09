
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
        print("Errore API:", e)
        return []

def main_loop():
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    notified_ids = load_notified_ids()
    live_events = get_live_events()
    if not live_events:
        print("⚠️ Nessun evento live disponibile.")
        return

    try:
        with open(MATCH_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    home = row["Home Team"].strip().lower()
                    away = row["Away Team"].strip().lower()
                    perc = float(row["FHG Over 0.5%"].replace('%', '').strip())
                    if perc < 30:
                        continue
                    for event in live_events:
                        if not event.get("time") or not event.get("home") or not event.get("away"):
                            continue
                        eh = event["home"].strip().lower()
                        ea = event["away"].strip().lower()
                        minute = int(event["time"].split("'")[0])
                        if (home in eh and away in ea) or (home in ea and away in eh):
                            if event["scores"]["1"]["home"] == "0" and event["scores"]["1"]["away"] == "0":
                                odds = event.get("odds", {}).get("1_1", {})
                                if not odds:
                                    continue
                                over_05 = float(odds.get("0_1", 0))
                                if over_05 >= 1.4:
                                    match_id = event["id"]
                                    if match_id in notified_ids:
                                        continue
                                    message = (
                                        f"⚠️ *PARTITA LIVE INTERESSANTE*\n"
                                        f"{event['league']['name']}\n"
                                        f"{event['home']} vs {event['away']}\n"
                                        f"🕒 Minuto: {minute}'\n"
                                        f"🔥 Over 0.5 HT: *{perc}%*\n"
                                        f"💸 Quota live: *{over_05}*"
                                    )
                                    send_telegram(message)
                                    save_notified_id(match_id)
                except Exception as err:
                    print("Errore elaborazione match:", err)
    except Exception as err:
        print("Errore lettura file CSV:", err)

if __name__ == "__main__":
    main_loop()
