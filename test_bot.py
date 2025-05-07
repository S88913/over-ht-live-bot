import time
from datetime import datetime
import pytz

def log_time():
    tz = pytz.timezone("Europe/Rome")
    while True:
        ora = datetime.now(tz).strftime('%H:%M:%S')
        print(f"🟢 Bot LIVE: check effettuato alle {ora}")
        time.sleep(15)

if __name__ == "__main__":
    log_time()
