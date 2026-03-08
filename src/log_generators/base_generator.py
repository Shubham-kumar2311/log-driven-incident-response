import json
import uuid
import random
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)


def generate_base_log(service_name, category, log_level, event_type, message, metadata):
    return {
        "event_id": str(uuid.uuid4()),   # ADD THIS
        "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "service_name": service_name,
        "category": category,
        "log_level": log_level,
        "event_type": event_type,
        "message": message,
        "trace_id": str(uuid.uuid4()),
        "span_id": uuid.uuid4().hex[:8],
        "host": "node-" + str(random.randint(1, 3)),
        "container_id": uuid.uuid4().hex[:12],
        "environment": "prod",
        "schema_version": "1.0",
        "metadata": metadata,
    }


def write_log(service_name, log_data):
    file_path = os.path.join(LOG_DIR, f"{service_name}.log")
    with open(file_path, "a") as f:
        f.write(json.dumps(log_data) + "\n")