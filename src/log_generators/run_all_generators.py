import sys
import logging
import threading

from config import MODE

from auth_service import run as auth_run
from api_gateway import run as api_run
from db_monitor import run as db_run
from deployment_service import run as deploy_run
from k8s_runtime import run as k8s_run
from worker_service import run as worker_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("log_generator")

GENERATORS = [
    ("auth-service", auth_run),
    ("api-gateway", api_run),
    ("db-service", db_run),
    ("deployment-service", deploy_run),
    ("k8s-runtime", k8s_run),
    ("worker-service", worker_run),
]


def main():
    mode = MODE
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    logger.info("Starting %d log generators in '%s' mode", len(GENERATORS), mode)

    threads = []
    for name, run_fn in GENERATORS:
        t = threading.Thread(target=run_fn, args=(mode,), name=name, daemon=True)
        t.start()
        threads.append(t)
        logger.info("Started generator: %s", name)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Shutting down generators")


if __name__ == "__main__":
    main()
