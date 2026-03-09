import random
import time
from base_generator import generate_base_log, write_log

SERVICE = "auth-service"


def run(mode="normal"):
    while True:
        ip = f"10.0.0.{random.randint(1,255)}"
        username = f"user_{random.randint(1000,9999)}"

        if mode == "error_spike" and random.random() < 0.6:
            success = False
        else:
            success = random.random() > 0.2

        if success:
            log = generate_base_log(
                SERVICE,
                "security",
                "INFO",
                "auth.login_success",
                f"User {username} logged in successfully",
                {"username": username, "client_ip": ip}
            )
        else:
            log = generate_base_log(
                SERVICE,
                "security",
                "WARN",
                "auth.login_failed",
                f"Failed login attempt for {username}",
                {"username": username, "client_ip": ip}
            )

        write_log(SERVICE, log)
        time.sleep(random.uniform(0.5, 1.5))