
import csv
import requests

# CONFIG
BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"
MATCH_FILE = "matches.csv"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        print("✅ Inviato:", r.json())
    except Exception as e:
        print("❌ Errore Telegram:", e)

def main():
    print("✅ TEST FORZATO AVVIATO")
    try:
        with open(MATCH_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                perc = float(row["Over05 FHG HT Average"])
                if perc >= 60:
                    msg = (
                        f"⚠️ *TEST NOTIFICA*
"
                        f"{row['Country']} – {row['League']}
"
                        f"{row['Home Team']} vs {row['Away Team']}
"
                        f"🔥 Over 0.5 HT: *{perc:.1f}%*"
                    )
                    send_telegram(msg)
                    break
    except Exception as e:
        print("❌ Errore:", e)

if __name__ == "__main__":
    main()
