import random
import time
from datetime import datetime

levels = ["stdout", "stderr"]
messages = [
    "ERROR database connection failed",
    "Retrying connection...",
    "Service started successfully"
]

while True:
    ts = datetime.utcnow().isoformat() + "Z"
    stream = random.choice(levels)
    msg = random.choice(messages)
    log = f"{ts} {stream} F {msg}"
    print(log)
    with open("k8s.log", "a") as f:
        f.write(log + "\n")
    time.sleep(0.7)
