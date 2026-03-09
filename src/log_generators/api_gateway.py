import random
import time
from base_generator import generate_base_log, write_log

SERVICE = "api-gateway"


def run(mode="normal"):
    paths = ["/api/v1/users", "/api/v1/orders", "/api/v1/payments"]

    while True:
        path = random.choice(paths)
        latency = random.randint(20, 150)

        if mode == "error_spike" and random.random() < 0.4:
            status = 500
            latency = random.randint(1000, 5000)
        else:
            status = 200

        log = generate_base_log(
            SERVICE,
            "application",
            "ERROR" if status >= 500 else "INFO",
            "http.request",
            f"{status} response for {path}",
            {
                "path": path,
                "status": status,
                "latency_ms": latency,
                "client_ip": f"10.0.1.{random.randint(1,255)}",
            },
        )

        write_log(SERVICE, log)
        time.sleep(random.uniform(0.3, 1.0))