import random
import time

services = ["auth-service", "payment-service", "order-service"]
levels = ["INFO", "WARN", "ERROR"]

messages = {
    "INFO": [
        "request processed successfully",
        "user authenticated",
        "order created"
    ],
    "WARN": [
        "retrying request",
        "slow response detected"
    ],
    "ERROR": [
        "timeout after 5 retries",
        "database connection failed",
        "null pointer exception"
    ]
}

def generate_log():
    service = random.choice(services)
    level = random.choices(levels, weights=[0.6, 0.25, 0.15])[0]
    msg = random.choice(messages[level])
    return f"{service} {level} {msg}"

def main(count: int = 5):
    with open("app.log", "a") as f:
        for _ in range(count):
            log = generate_log()
            print(log)
            f.write(log + "\n")
            time.sleep(0.5)


if __name__ == "__main__":
    main(5)
