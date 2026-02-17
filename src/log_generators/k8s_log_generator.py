import random
import time

levels = ["stdout", "stderr"]
messages = [
    "ERROR database connection failed",
    "Retrying connection...",
    "Service started successfully"
]


def main(count: int = 5):
    with open("app.log", "a") as f:
        for _ in range(count):
            stream = random.choice(levels)
            msg = random.choice(messages)
            log = f"{stream} F {msg}"
            print(log)
            f.write(log + "\n")
            time.sleep(0.2)


if __name__ == "__main__":
    main(5)
