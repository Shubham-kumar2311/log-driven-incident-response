import random
from base_generator import generate_base_log, write_log, sleep_between_logs

SERVICE = "k8s-runtime"

PODS = ["auth-service-pod", "api-gateway-pod", "worker-pod", "db-proxy-pod", "cache-pod"]
NAMESPACES = ["default", "production", "staging"]


def run(mode="normal"):
    while True:
        pod = random.choice(PODS)
        ns = random.choice(NAMESPACES)

        if mode in ("crash_loop", "error_spike") and random.random() < 0.5:
            event = "pod.oom_killed"
            level = "ERROR"
            msg = f"Pod {pod} OOMKilled in {ns}"
            meta = {"pod": pod, "namespace": ns, "reason": "OOMKilled",
                    "memory_limit_mb": 512, "memory_usage_mb": random.randint(512, 800),
                    "restart_count": random.randint(1, 10)}
        elif random.random() < 0.08:
            event = random.choice(["pod.crash_loop", "pod.evicted"])
            level = "ERROR"
            msg = f"Pod {pod} {event.split('.')[1]} in {ns}"
            meta = {"pod": pod, "namespace": ns, "reason": event.split(".")[1],
                    "restart_count": random.randint(1, 15)}
        else:
            event = "pod.running"
            level = "INFO"
            msg = f"Pod {pod} healthy in {ns}"
            meta = {"pod": pod, "namespace": ns, "cpu_pct": round(random.uniform(5, 80), 1),
                    "memory_pct": round(random.uniform(20, 70), 1)}

        log = generate_base_log(SERVICE, "infrastructure", level, event, msg, meta)
        write_log(SERVICE, log)
        sleep_between_logs()
