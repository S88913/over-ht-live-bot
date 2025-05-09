
import csv
import requests
import time
from datetime import datetime
import pytz
import os

BETSAPI_KEY = "INSERISCI_LA_TUA_API_KEY"
BOT_TOKEN = "INSERISCI_IL_TOKEN_DEL_BOT"
CHAT_ID = "INSERISCI_IL_TUO_CHAT_ID"
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
        print("❌ Errore eventi live:", e)
        return []

def get_1st_half_over05_odds(event_id):
    url = f"https://api.b365api.com/v1/bet365/event?token={BETSAPI_KEY}&event_id={event_id}"
    try:
        res = requests.get(url)
        markets = res.json().get("results", {}).get("odds", [])
        for m in markets:
            if m.get("name") == "1st Half - Over/Under":
                for o in m.get("main", []):
                    if o.get("name") == "Over 0.5":
                        return float(o.get("odds"))
    except:
        return None
    return None

def main():
    print("✅ SCRIPT AVVIATO – controllo iniziale")
    notified = load_notified_ids()
    events = get_live_events()

    if not events:
        print("⚠️ Nessun evento live disponibile.")
        return

    try:
        with open(MATCH_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    perc_str = row.get("Over05 FHG HT Average", "").replace("%", "").strip()
                    if not perc_str:
                        continue
                    perc = float(perc_str)
                    if perc < 30:  # soglia abbassata per test
                        continue

                    home = row["Home Team"].strip().lower()
                    away = row["Away Team"].strip().lower()
                    match_time = row["date_GMT"].split(" - ")[-1]

                    for ev in events:
                        home_live = ev.get("home", {}).get("name", "").lower()
                        away_live = ev.get("away", {}).get("name", "").lower()

                        if home in home_live and away in away_live:
                            match_id = ev["id"]
                            if match_id in notified:
                                continue

                            minute = int(ev.get("time", {}).get("tm", 0))
                            score = ev.get("ss", "0-0")
                            if score != "0-0":
                                continue

                            odds = get_1st_half_over05_odds(match_id)

                            if odds is not None and odds >= 1.40:
                                msg = (
                                    f"⚠️ *PARTITA DA MONITORARE LIVE*
"
                                    f"{row['Country']} – {row['League']}
"
                                    f"{row['Home Team']} vs {row['Away Team']}
"
                                    f"🕒 Orario: {match_time}
"
                                    f"🔥 Over 0.5 HT: *{perc:.1f}%* – Quota: {odds}"
                                )
                                send_telegram(msg)
                                save_notified_id(match_id)
                            break
                except Exception as e:
                    print("⚠️ Errore elaborazione match:", e)
    except FileNotFoundError:
        print("❌ File matches.csv mancante.")

if __name__ == "__main__":
    main()
