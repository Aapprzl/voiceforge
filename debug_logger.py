import datetime
import os

LOG_FILE = "debug_log.txt"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            f.flush()
            os.fsync(f.fileno())
    except:
        pass

def clear_log():
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except:
        pass
