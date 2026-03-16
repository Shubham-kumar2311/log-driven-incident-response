import random
from base_generator import generate_base_log, write_log, sleep_between_logs

SERVICE = "deployment-service"

SERVICES_DEPLOYED = ["auth-service", "api-gateway", "db-service", "worker-service", "notification-service"]


def run(mode="normal"):
    while True:
        target = random.choice(SERVICES_DEPLOYED)
        version = f"v{random.randint(1,5)}.{random.randint(0,20)}.{random.randint(0,99)}"

        if mode == "error_spike" and random.random() < 0.3:
            success = False
        elif random.random() < 0.05:
            success = False
        else:
            success = True

        if success:
            log = generate_base_log(
                SERVICE, "deployment", "INFO", "deployment.success",
                f"Deployed {target}:{version} successfully",
                {"target_service": target, "version": version,
                 "duration_sec": random.randint(15, 120), "rollback": False}
            )
        else:
            reason = random.choice(["health_check_failed", "timeout", "image_pull_error", "resource_limit"])
            log = generate_base_log(
                SERVICE, "deployment", "ERROR", "deployment.failed",
                f"Deployment of {target}:{version} failed: {reason}",
                {"target_service": target, "version": version, "reason": reason}
            )

        write_log(SERVICE, log)
        sleep_between_logs()
