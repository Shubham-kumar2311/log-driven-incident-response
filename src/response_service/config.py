import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

# Redis Configuration
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Service API
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8005"))
CORS_ORIGINS = _csv_env(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8005",
)
ACTUATOR_API_URL = os.getenv("ACTUATOR_API_URL", "http://localhost:8007")

# Redis Channels/Streams
INCIDENT_STREAM = os.getenv("INCIDENT_STREAM", "incident_events")
RESPONSE_STREAM = os.getenv("RESPONSE_STREAM", "response_events")
ACTUATOR_STREAM = os.getenv("ACTUATOR_STREAM", "actuator_events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "response_service_group")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "response_worker_1")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "incident_response")
PLAYBOOKS_COLLECTION = os.getenv("PLAYBOOKS_COLLECTION", "playbooks")

# Action Execution Config
ACTION_TIMEOUT_SECONDS = int(os.getenv("ACTION_TIMEOUT_SECONDS", 30))
ACTION_MAX_RETRIES = int(os.getenv("ACTION_MAX_RETRIES", 3))
ACTION_RETRY_DELAY_SECONDS = float(os.getenv("ACTION_RETRY_DELAY_SECONDS", 1.0))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
