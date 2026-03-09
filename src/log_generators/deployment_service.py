import random
import time
from base_generator import generate_base_log, write_log

SERVICE = "deployment-service"


def run(mode="normal"):
    while True:
        version = f"v0.{random.randint(1,5)}.{random.randint(1,99)}"

        if mode == "error_spike" and random.random() < 0.3:
            event = "deployment.failed"
            level = "ERROR"
            message = f"Deployment {version} failed health check"
        else:
            event = "deployment.rolled_out"
            level = "INFO"
            message = f"Deployment {version} rolled out"

        log = generate_base_log(
            SERVICE,
            "deployment",
            level,
            event,
            message,
            {"version": version},
        )

        write_log(SERVICE, log)
        time.sleep(random.uniform(2, 5))