import random
from base_generator import generate_base_log, write_log, sleep_between_logs

SERVICE = "worker-service"

JOBS = ["email_send", "report_generate", "data_export", "cache_rebuild", "log_archive"]


def run(mode="normal"):
    while True:
        job = random.choice(JOBS)
        duration = random.randint(100, 5000)

        if mode == "error_spike" and random.random() < 0.4:
            level = "ERROR"
            event = "worker.job_failed"
            reason = random.choice(["timeout", "oom", "dependency_error", "rate_limited"])
            msg = f"Job {job} failed: {reason}"
            meta = {"job": job, "duration_ms": duration, "reason": reason,
                    "retries": random.randint(0, 3)}
        elif random.random() < 0.05:
            level = "WARN"
            event = "worker.job_slow"
            duration = random.randint(5000, 30000)
            msg = f"Job {job} slow: {duration}ms"
            meta = {"job": job, "duration_ms": duration}
        else:
            level = "INFO"
            event = "worker.job_completed"
            msg = f"Job {job} completed in {duration}ms"
            meta = {"job": job, "duration_ms": duration, "result_count": random.randint(1, 1000)}

        log = generate_base_log(SERVICE, "background", level, event, msg, meta)
        write_log(SERVICE, log)
        sleep_between_logs()
