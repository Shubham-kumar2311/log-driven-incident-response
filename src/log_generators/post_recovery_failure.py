import time
from datetime import datetime

service = "auth-service"

def log(level, msg):
    ts = datetime.now().strftime("%b %d %H:%M:%S")
    line = f"{ts} {service} {level} {msg}"
    print(line)
    with open("app.log", "a") as f:
        f.write(line + "\n")

# Known error
for _ in range(3):
    log("ERROR", "timeout after 5 retries")
    time.sleep(0.5)

# Simulate recovery
log("INFO", "service restarted successfully")
time.sleep(1)

# Unknown error
log("ERROR", "segmentation fault at address 0x0000")
