import json
import uuid
import random
import os
import time
import logging
import requests
from datetime import datetime, timezone

from config import LOG_DIR, OUTPUT_MODE, HTTP_INGESTION_URL, REDIS_HOST, REDIS_PORT, REDIS_STREAM, LOG_RATE_MIN, LOG_RATE_MAX

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("log_generator")

_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        import redis
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return _redis_client


def generate_base_log(service_name, category, log_level, event_type, message, metadata):
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "service_name": service_name,
        "service": service_name,
        "category": category,
        "log_level": log_level,
        "level": log_level,
        "event_type": event_type,
        "event": event_type,
        "message": message,
        "trace_id": str(uuid.uuid4()),
        "span_id": uuid.uuid4().hex[:8],
        "host": "node-" + str(random.randint(1, 5)),
        "container_id": uuid.uuid4().hex[:12],
        "environment": "prod",
        "schema_version": "1.0",
        "metadata": metadata or {},
    }


def write_log(service_name, log_data):
    if OUTPUT_MODE == "http":
        _send_http(log_data)
    elif OUTPUT_MODE == "redis":
        _send_redis(log_data)
    else:
        _write_file(service_name, log_data)


def _write_file(service_name, log_data):
    file_path = os.path.join(LOG_DIR, f"{service_name}.log")
    try:
        with open(file_path, "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except OSError as e:
        logger.error("Failed writing log to %s: %s", file_path, e)


def _send_http(log_data):
    for attempt in range(3):
        try:
            resp = requests.post(HTTP_INGESTION_URL, json=log_data, timeout=3)
            if resp.status_code < 300:
                return
            logger.warning("HTTP ingestion returned %d", resp.status_code)
        except requests.RequestException as e:
            logger.warning("HTTP send attempt %d failed: %s", attempt + 1, e)
        time.sleep(0.5 * (attempt + 1))
    logger.error("Failed to send log via HTTP after 3 attempts")


def _send_redis(log_data):
    try:
        client = _get_redis_client()
        client.xadd(REDIS_STREAM, {"data": json.dumps(log_data)})
    except Exception as e:
        logger.error("Redis send failed: %s", e)


def sleep_between_logs():
    time.sleep(random.uniform(LOG_RATE_MIN, LOG_RATE_MAX))
