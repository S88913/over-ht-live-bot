import os
import requests
import time
import logging
from datetime import datetime

# === CONFIGURAZIONE ===
BETSAPI_KEY = os.getenv("BETSAPI_KEY")  # Esempio: "dbc60aec3b60b57175815ab6f1477348"
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY")  # La tua chiave FootyStats
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Token del bot Telegram da @BotFather
CHAT_ID = os.getenv("CHAT_ID")  # ID della chat dove inviare messaggi
NOTIFIED_FILE = "notified_live.txt"  # File per tracciare le notifiche

MIN_PERCENTAGE = 60  # Soglia minima percentuale Over 0.5 HT
MIN_ODDS = 1.50  # Soglia minima quota

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
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Notifica inviata: {message[:50]}...")  # Log parziale per brevità
    except Exception as e:
        logging.error(f"Errore Telegram: {str(e)}")

def load_notified_ids():
    """Carica gli ID delle partite già notificate."""
    try:
        if os.path.exists(NOTIFIED_FILE):
            with open(NOTIFIED_FILE, "r") as f:
                return set(line.strip() for line in f)
        return set()
    except Exception as e:
        logging.error(f"Errore caricamento notified IDs: {str(e)}")
        return set()

def save_notified_id(match_id):
    """Salva un nuovo ID nel file delle notifiche."""
    try:
        with open(NOTIFIED_FILE, "a") as f:
            f.write(f"{match_id}\n")
    except Exception as e:
        logging.error(f"Errore salvataggio ID: {str(e)}")

def get_live_events():
    """Ottiene le partite in corso da BETSAPI."""
    url = f"https://api.b365api.com/v3/events/inplay?sport_id=1&token={BETSAPI_KEY}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get("results", [])
        logging.error(f"BETSAPI error: HTTP {response.status_code}")
        return []
    except Exception as e:
        logging.error(f"Errore BETSAPI: {str(e)}")
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
        logging.error(f"Errore quote: {str(e)}")
        return None

def get_footystats_matches():
    """Ottiene i dati da FootyStats API."""
    url = "https://api.footystats.org/your_endpoint"  # Sostituisci con l'endpoint vero
    params = {"key": FOOTYSTATS_API_KEY, "season": "2023/24"}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", [])
        logging.error(f"FootyStats error: HTTP {response.status_code}")
        return []
    except Exception as e:
        logging.error(f"Errore FootyStats: {str(e)}")
        return []

def main():
    logging.info("=== AVVIO BOT ===")
    notified = load_notified_ids()
    live_events = get_live_events()
    stats_matches = get_footystats_matches()

    if not live_events:
        logging.info("Nessuna partita live trovata.")
        return

    for match in stats_matches:
        try:
            home = match.get("home_team", "").lower()
            away = match.get("away_team", "").lower()
            percentage = float(match.get("over_0.5_first_half_percentage", 0))

            if percentage < MIN_PERCENTAGE:
                continue

            for event in live_events:
                event_home = event.get("home", {}).get("name", "").lower()
                event_away = event.get("away", {}).get("name", "").lower()
                event_id = str(event.get("id"))
                score = event.get("ss", "0-0")

                if (home in event_home and away in event_away
                    and event_id not in notified
                    and score == "0-0"):

                    odds = get_odds(event_id)
                    if odds and odds >= MIN_ODDS:
                        minute = event.get("time", {}).get("tm", "?")
                        msg = (
                            f"⚠️ *LIVE TRACKING*\n"
                            f"🏆 {match.get('league_name', 'N/A')}\n"
                            f"⚽ {match.get('home_team')} vs {match.get('away_team')}\n"
                            f"⏱️ {minute}' | Score: {score}\n"
                            f"📊 Over 0.5 HT: *{percentage:.1f}%*\n"
                            f"💰 Odds: {odds}"
                        )
                        send_telegram(msg)
                        save_notified_id(event_id)
                        break
        except Exception as e:
            logging.error(f"Errore elaborazione match: {str(e)}")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(300)  # Controlla ogni 5 minuti
