
import csv
import requests
import time
from datetime import datetime
import pytz
import os
import re

# === CONFIG ===
BETSAPI_KEY = "dbc60aec3b60b57175815ab6f1477348"
BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"
NOTIFIED_FILE = "notified_live.txt"
MATCH_FILE = "matches_expanded.csv"
PERC_MINIMA = 60.0
QUOTA_MINIMA = 1.50

def normalize_team_name(name):
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name.lower()

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
                    perc_str = row["Over05 FHG HT Average"].replace("%", "").strip()
                    perc = float(perc_str)
                    if perc < PERC_MINIMA:
                        continue

                    home_csv = normalize_team_name(row["Home Team"])
                    away_csv = normalize_team_name(row["Away Team"])

                    for ev in events:
                        home_live = normalize_team_name(ev.get("home", {}).get("name", ""))
                        away_live = normalize_team_name(ev.get("away", {}).get("name", ""))

                        if home_csv in home_live and away_csv in away_live:
                            match_id = ev["id"]
                            if match_id in notified:
                                continue

                            minute = int(ev.get("time", {}).get("tm", 0))
                            score = ev.get("ss", "0-0")
                            if score != "0-0":
                                continue

                            quota = get_1st_half_over05_odds(match_id)
                            if quota is None or quota < QUOTA_MINIMA:
                                continue

                            msg = (
                                f"⚠️ *PARTITA DA MONITORARE LIVE*\n"
                                f"{row['Country']} – {row['League']}\n"
                                f"{row['Home Team']} vs {row['Away Team']}\n"
                                f"🕒 Minuto: {minute} – Risultato: {score}\n"
                                f"🔥 Over 0.5 HT: *{perc:.1f}%* – Quota: {quota}"
                            )
                            send_telegram(msg)
                            save_notified_id(match_id)
                            break
                except Exception as e:
                    print("⚠️ Riga saltata:", e)
    except FileNotFoundError:
        print("❌ File matches_expanded.csv mancante.")

if __name__ == "__main__":
    main()
