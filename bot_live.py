import requests

BOT_TOKEN = "7892082434:AAF0fZpY1ZCsawGVLDtrGXUbeYWUoCn37Zg"
CHAT_ID = "6146221712"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data)
        print("✅ Inviato:", r.json())
    except Exception as e:
        print("❌ Errore Telegram:", e)

def main():
    print("✅ SCRIPT TEST AVVIATO – invio notifica singola")
    msg = (
        "⚠️ *TEST NOTIFICA*\n"
        "Questa è una prova di messaggio automatico del bot live.\n"
        "Se stai leggendo questo, il sistema funziona correttamente!"
    )
    send_telegram(msg)

if __name__ == "__main__":
    main()