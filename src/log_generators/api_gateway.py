import random
from base_generator import generate_base_log, write_log, sleep_between_logs

SERVICE = "api-gateway"

PATHS = ["/api/v1/users", "/api/v1/orders", "/api/v1/payments",
         "/api/v1/products", "/api/v1/health", "/api/v2/search"]
METHODS = ["GET", "POST", "PUT", "DELETE"]


def run(mode="normal"):
    while True:
        path = random.choice(PATHS)
        method = random.choice(METHODS)
        latency = random.randint(15, 200)

        if mode == "error_spike" and random.random() < 0.4:
            status = random.choice([500, 502, 503])
            latency = random.randint(1000, 5000)
        elif random.random() < 0.05:
            status = random.choice([400, 401, 403, 404, 429])
            latency = random.randint(50, 300)
        else:
            status = 200

        level = "ERROR" if status >= 500 else ("WARN" if status >= 400 else "INFO")

        log = generate_base_log(
            SERVICE, "application", level, "http.request",
            f"{method} {path} -> {status} ({latency}ms)",
            {"path": path, "method": method, "status": status,
             "latency_ms": latency, "client_ip": f"10.0.1.{random.randint(1,255)}"}
        )

        write_log(SERVICE, log)
        sleep_between_logs()
