import random
from base_generator import generate_base_log, write_log, sleep_between_logs

SERVICE = "auth-service"


def run(mode="normal"):
    while True:
        ip = f"10.0.{random.randint(0,5)}.{random.randint(1,255)}"
        username = random.choice(["admin", "root", "deploy-bot", "svc-account",
                                  f"user_{random.randint(1000,9999)}"])

        if mode == "error_spike" and random.random() < 0.6:
            success = False
        else:
            success = random.random() > 0.15

        if success:
            log = generate_base_log(
                SERVICE, "security", "INFO", "auth.login_success",
                f"User {username} logged in from {ip}",
                {"username": username, "client_ip": ip, "method": random.choice(["password", "sso", "api_key"])}
            )
        else:
            reason = random.choice(["invalid_password", "account_locked", "expired_token", "invalid_mfa"])
            log = generate_base_log(
                SERVICE, "security", "WARN", "auth.login_failed",
                f"Login failed for {username}: {reason}",
                {"username": username, "client_ip": ip, "reason": reason}
            )

        write_log(SERVICE, log)
        sleep_between_logs()
