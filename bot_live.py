import os
import requests
import time
from datetime import datetime
import pytz
import logging

# === CONFIGURAZIONE ===
BETSAPI_KEY = os.getenv("BETSAPI_KEY", "dbc60aec3b60b57175815ab6f1477348")  # Sostituisci con la tua chiave
FOOTYSTATS_API_KEY = os.getenv("FOOTYSTATS_API_KEY", "tua_chiave_footystats")  # Ottieni da FootyStats
BOT_TOKEN = os.getenv("BOT_TOKEN", "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg")  # Da @BotFather
CHAT_ID = os.getenv("CHAT_ID", "6146221712")  # ID della chat Telegram
NOTIFIED_FILE = "notified_live.txt"  # File per tenere traccia delle partite già notificate

# Soglie per filtrare le partite
MIN_PERCENTAGE = 60  # Percentuale minima Over 0.5 primo tempo
MIN_ODDS = 1.50  # Quota minima

# Configurazione logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === FUNZIONI PRINCIPALI ===
def send_telegram(message):
    """Invia un messaggio a Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logging.info(f"Notifica inviata: {message}")
        else:
            logging.error(f"Errore Telegram API: {response.text}")
    except Exception as e:
        logging.error(f"Errore connessione Telegram: {e}")

def load_notified_ids():
    """Carica gli ID delle partite già notificate."""
    if not os.path.exists(NOTIFIED_FILE):
        return set()
    with open(NOTIFIED_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_notified_id(match_id):
    """Salva un nuovo ID nel file delle notifiche."""
    with open(NOTIFIED_FILE, "a") as f:
        f.write(f"{match_id}\n")

def get_live_events():
    """Ottiene le partite in corso da BETSAPI."""
    url = f"https://api.b365api.com/v3/events/inplay?sport_id=1&token={BETSAPI_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            logging.error(f"BETSAPI error: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Errore connessione BETSAPI: {e}")
        return []

def get_1st_half_over05_odds(event_id):
    """Recupera la quota Over 0.5 primo tempo da BETSAPI."""
    url = f"https://api.b365api.com/v1/bet365/event?token={BETSAPI_KEY}&event_id={event_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            markets = response.json().get("results", {}).get("odds", [])
            for market in markets:
                if market.get("name") == "1st Half - Over/Under":
                    for odds in market.get("main", []):
                        if odds.get("name") == "Over 0.5":
                            return float(odds.get("odds", 0))
        return None
    except Exception as e:
        logging.error(f"Errore quota Over 0.5: {e}")
        return None

def get_footystats_matches():
    """Ottiene le partite con statistiche Over 0.5 HT da FootyStats."""
    url = "https://api.footystats.org/endpoint_over05_ht"  # Sostituisci con l'endpoint corretto
    params = {
        "key": FOOTYSTATS_API_KEY,
        "season": "2023/24",  # Modifica in base alla stagione
        "league_id": "1234"    # Filtra per campionato (opzionale)
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            logging.error(f"FootyStats API error: {response.text}")
            return []
    except Exception as e:
        logging.error(f"Errore connessione FootyStats: {e}")
        return []

# === LOGICA PRINCIPALE ===
def main():
    notified = load_notified_ids()
    live_events = get_live_events()
    footystats_matches = get_footystats_matches()

    if not live_events:
        logging.info("Nessuna partita in corso trovata.")
        return

    for match in footystats_matches:
        try:
            home_team = match.get("home_team", "").lower()
            away_team = match.get("away_team", "").lower()
            over05_percentage = float(match.get("over_0.5_first_half_percentage", 0))

            if over05_percentage < MIN_PERCENTAGE:
                continue

            # Cerca corrispondenze nelle partite live
            for event in live_events:
                event_home = event.get("home", {}).get("name", "").lower()
                event_away = event.get("away", {}).get("name", "").lower()
                event_id = event.get("id")
                score = event.get("ss", "0-0")

                if (home_team in event_home and away_team in event_away
                    and event_id not in notified
                    and score == "0-0"):

                    odds = get_1st_half_over05_odds(event_id)
                    if odds and odds >= MIN_ODDS:
                        minute = event.get("time", {}).get("tm", "0")
                        message = (
                            f"⚠️ *PARTITA DA MONITORARE LIVE*\n"
                            f"🏆 {match.get('league_name', 'N/A')}\n"
                            f"⚽ {match.get('home_team')} vs {match.get('away_team')}\n"
                            f"🕒 Minuto: {minute} – Risultato: {score}\n"
                            f"📊 Over 0.5 HT: *{over05_percentage:.1f}%*\n"
                            f"💰 Quota: {odds}"
                        )
                        send_telegram(message)
                        save_notified_id(event_id)
                        break  # Passa alla prossima partita

        except Exception as e:
            logging.error(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(300)  # Controlla ogni 5 minuti
