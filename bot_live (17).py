import csv
import time
import os

print("✅ SCRIPT AVVIATO – controllo iniziale")

MATCH_FILE = "matches.csv"

# Verifica se esiste il file
if not os.path.exists(MATCH_FILE):
    print("❌ ERRORE: File matches.csv NON trovato.")
else:
    print("📁 File matches.csv trovato.")
    with open(MATCH_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"📊 Righe trovate: {len(rows)}")
        for row in rows:
            try:
                home = row.get("Home Team", "N/A")
                away = row.get("Away Team", "N/A")
                perc = row.get("Over05 FHG HT Average", "N/A")
                print(f"⚽ Match: {home} vs {away} | Over05 HT: {perc}")
            except Exception as e:
                print("⚠️ Errore nella riga:", e)

print("✅ FINE TEST BOT")