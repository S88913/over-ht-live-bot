import csv
import requests
import time
from datetime import datetime
import pytz
import os
from difflib import SequenceMatcher

# === CONFIG ===
BETSAPI_KEY = "dbc60aec3b60b57175815ab6f1477348"
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

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def main():
    print("🔍 Controllo in corso...")
    notified = load_notified_ids()
    events = get_live_events()

    if not events:
        print("⚠️ Nessun evento live disponibile.")
        return

    print(f"📺 Eventi live trovati: {len(events)}")
    try:
        with open(MATCH_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    perc_str = row["Over05 FHG HT Average"].replace("%", "").strip()
                    perc = float(perc_str)
                    if perc < 85:
                        continue

                    home = row["Home Team"].strip().lower()
                    away = row["Away Team"].strip().lower()

                    for ev in events:
                        home_live = ev.get("home", {}).get("name", "").lower()
                        away_live = ev.get("away", {}).get("name", "").lower()

                        print(f"🔄 LIVE: {home_live} vs {away_live}")

                        home_sim = similar(home, home_live)
                        away_sim = similar(away, away_live)

                        if home_sim >= 0.7 and away_sim >= 0.7:
                            match_id = ev["id"]
                            if match_id in notified:
                                continue

                            minute = int(ev.get("time", {}).get("tm", 0))
                            score = ev.get("ss", "0-0")
                            if score != "0-0":
                                continue

                            quota = get_1st_half_over05_odds(match_id)

                            if minute >= 20 or (quota is not None and quota >= 2.00):
                                msg = (
                                    f"⚠️ *PARTITA DA MONITORARE LIVE*\n"
                                    f"{row['Country']} – {row['League']}\n"
                                    f"{row['Home Team']} vs {row['Away Team']}\n"
                                    f"🕒 Minuto: {minute} – Risultato: {score}\n"
                                    f"🔥 Over 0.5 HT: *{perc:.1f}%*"
                                )
                                if quota:
                                    msg += f" – Quota: {quota}"

                                send_telegram(msg)
                                save_notified_id(match_id)
                            break
                except Exception as e:
                    print("⚠️ Riga saltata:", e)
    except FileNotFoundError:
        print("❌ File matches.csv mancante.")

if __name__ == "__main__":
    last_hour = None
    while True:
        main()
        current_time = datetime.now().strftime('%H')
        if current_time != last_hour:
            send_telegram(f"🔄 Bot attivo – controllo OK alle {datetime.now().strftime('%H:%M')}")
            last_hour = current_time
        time.sleep(30)
