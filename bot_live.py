import os
import requests
import time
import logging
from datetime import datetime

# === CONFIGURAZIONE ===
BETSAPI_KEY = "220574-Me4itoG4ZYLWQ3"
FOOTYSTATS_API_KEY = "972183dce49bfd4d567da3d61e8ab389b2e04334728101dcc4ba28f9d4f4d19e"
BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"
NOTIFIED_FILE = "notified_live.txt"

MIN_PERCENTAGE = 60  # Soglia minima percentuale Over 0.5 HT
MIN_ODDS = 1.50      # Soglia minima quota

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

def send_telegram(message):
    """Invia un messaggio a Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"📤 Notifica inviata: {message[:50]}...")
    except Exception as e:
        logging.error(f"❌ Errore Telegram: {str(e)}")

def load_notified_ids():
    """Carica gli ID delle partite già notificate."""
    try:
        if os.path.exists(NOTIFIED_FILE):
            with open(NOTIFIED_FILE, "r") as f:
                return set(line.strip() for line in f)
        return set()
    except Exception as e:
        logging.error(f"❌ Errore caricamento ID: {str(e)}")
        return set()

def save_notified_id(match_id):
    """Salva un nuovo ID nel file delle notifiche."""
    try:
        with open(NOTIFIED_FILE, "a") as f:
            f.write(f"{match_id}\n")
    except Exception as e:
        logging.error(f"❌ Errore salvataggio ID: {str(e)}")

def get_live_events():
    """Ottiene le partite in corso da BETSAPI."""
    url = f"https://api.b365api.com/v3/events/inplay?sport_id=1&token={BETSAPI_KEY}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get("results", [])
        logging.error(f"❌ BETSAPI error: HTTP {response.status_code}")
        return []
    except Exception as e:
        logging.error(f"❌ Errore BETSAPI: {str(e)}")
        return []

def get_odds(event_id):
    """Recupera le quote Over 0.5 primo tempo."""
    url = f"https://api.b365api.com/v1/bet365/event?token={BETSAPI_KEY}&event_id={event_id}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            markets = response.json().get("results", {}).get("odds", [])
            for market in markets:
                if market.get("name") == "1st Half - Over/Under":
                    for odds in market.get("main", []):
                        if odds.get("name") == "Over 0.5":
                            return float(odds.get("odds", 0))
        return None
    except Exception as e:
        logging.error(f"❌ Errore quote: {str(e)}")
        return None

def get_footystats_matches():
    """Ottiene i dati da FootyStats API."""
    url = "https://api.footystats.org/league-matches"
    params = {
        "key": FOOTYSTATS_API_KEY,
        "season": "2023/24"  # Modifica in base alla stagione
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", [])
        logging.error(f"❌ FootyStats error: HTTP {response.status_code}")
        return []
    except Exception as e:
        logging.error(f"❌ Errore FootyStats: {str(e)}")
        return []

def main():
    logging.info("=== 🚀 AVVIO BOT ===")
    notified = load_notified_ids()
    live_events = get_live_events()
    stats_matches = get_footystats_matches()

    if not live_events:
        logging.info("⚠️ Nessuna partita live trovata.")
        return

    for match in stats_matches:
        try:
            home_team = match.get("home_name", "").lower()
            away_team = match.get("away_name", "").lower()
            over05_percentage = float(match.get("over_0_5_ht_percentage", 0))

            if over05_percentage < MIN_PERCENTAGE:
                continue

            for event in live_events:
                event_home = event.get("home", {}).get("name", "").lower()
                event_away = event.get("away", {}).get("name", "").lower()
                event_id = str(event.get("id"))
                score = event.get("ss", "0-0")

                if (home_team in event_home and away_team in event_away
                    and event_id not in notified
                    and score == "0-0"):

                    odds = get_odds(event_id)
                    if odds and odds >= MIN_ODDS:
                        minute = event.get("time", {}).get("tm", "?")
                        message = (
                            f"⚠️ *PARTITA DA MONITORARE LIVE*\n"
                            f"🏆 {match.get('league_name', 'N/A')}\n"
                            f"⚽ {match.get('home_name')} vs {match.get('away_name')}\n"
                            f"⏱️ Minuto: {minute}' | Risultato: {score}\n"
                            f"📊 Over 0.5 HT: *{over05_percentage:.1f}%*\n"
                            f"💰 Quota: {odds}"
                        )
                        send_telegram(message)
                        save_notified_id(event_id)
                        break
        except Exception as e:
            logging.error(f"❌ Errore elaborazione match: {str(e)}")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(300)  # Controlla ogni 5 minuti
