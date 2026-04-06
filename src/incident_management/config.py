import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

_service_dir = Path(__file__).resolve().parent
load_dotenv(_service_dir / ".env")


def _csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

# ── Redis ───────────────────────────────────────────────────────────
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ── Redis Streams ───────────────────────────────────────────────────
INPUT_STREAM = os.getenv("INPUT_STREAM", "detection_signals")
OUTPUT_CHANNEL = os.getenv("OUTPUT_CHANNEL", "incident_events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "incident-group")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "incident-mgr-1")

# ── Service API ──────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8004"))
CORS_ORIGINS = _csv_env(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8004",
)

# ── MongoDB ─────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "incident_management")
USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"

# ── Correlation ─────────────────────────────────────────────────────
CORRELATION_WINDOW_SECONDS = int(os.getenv("CORRELATION_WINDOW_SECONDS", 300))

# ── Severity ────────────────────────────────────────────────────────
CRITICAL_RISK_THRESHOLD = float(os.getenv("CRITICAL_RISK_THRESHOLD", 0.9))
CRITICAL_SIGNAL_COUNT = int(os.getenv("CRITICAL_SIGNAL_COUNT", 5))
HIGH_SIGNAL_COUNT = int(os.getenv("HIGH_SIGNAL_COUNT", 3))

# ── Service Criticality (comma-separated list of critical services)
CRITICAL_SERVICES = [
    s.strip()
    for s in os.getenv("CRITICAL_SERVICES", "auth-service,payment-service,database").split(",")
    if s.strip()
]

# ── Forwarding (to response service) ────────────────────────────────
FORWARD_URL = os.getenv("FORWARD_URL", "")

# ── Logging ─────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
