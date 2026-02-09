import time
from datetime import datetime

service = "auth-service"

def log(msg):
    ts = datetime.now().strftime("%b %d %H:%M:%S")
    line = f"{ts} {service} ERROR {msg}"
    print(line)
    with open("app.log", "a") as f:
        f.write(line + "\n")

# Normal behavior
for _ in range(5):
    log("request processed successfully")
    time.sleep(1)

# Error spike
for _ in range(10):
    log("timeout after 5 retries")
    time.sleep(0.2)
