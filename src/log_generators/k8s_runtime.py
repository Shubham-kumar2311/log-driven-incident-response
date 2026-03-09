import random
import time
from base_generator import generate_base_log, write_log

SERVICE = "k8s-runtime"


def run(mode="normal"):
    while True:
        if mode == "crash_loop" and random.random() < 0.5:
            event = "k8s.pod_oom_killed"
            level = "CRITICAL"
            message = "Pod killed due to OOM"
            metadata = {"memory_used_mb": random.randint(600, 900)}
        else:
            event = "k8s.pod_running"
            level = "INFO"
            message = "Pod running normally"
            metadata = {"cpu_percent": random.uniform(20, 70)}

        log = generate_base_log(
            SERVICE,
            "infra",
            level,
            event,
            message,
            metadata,
        )

        write_log(SERVICE, log)
        time.sleep(random.uniform(1, 3))