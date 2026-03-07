import random
import time
from base_generator import generate_base_log, write_log

SERVICE = "db-monitor"


def run(mode="normal"):
    while True:
        latency = random.randint(10, 200)

        if mode == "error_spike" and random.random() < 0.5:
            latency = random.randint(800, 2000)
            level = "ERROR"
            event = "db.slow_query"
        else:
            level = "INFO"
            event = "db.query"

        log = generate_base_log(
            SERVICE,
            "database",
            level,
            event,
            f"Query executed in {latency}ms",
            {"latency_ms": latency},
        )

        write_log(SERVICE, log)
        time.sleep(random.uniform(0.5, 1.5))