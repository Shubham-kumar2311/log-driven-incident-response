import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Redis ───────────────────────────────────────────────────────────
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ── Streams ─────────────────────────────────────────────────────────
INPUT_STREAM = "processed_logs"
OUTPUT_STREAM = "detection_signals"
CONSUMER_GROUP = "detection-group"
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "detector-1")

# ── Rulebook ────────────────────────────────────────────────────────
_service_dir = Path(__file__).resolve().parent
RULEBOOK_PATH = os.getenv("RULEBOOK_PATH", str(_service_dir / "rulebook.json"))

# ── Logging ─────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Anomaly Engine ──────────────────────────────────────────────────
ANOMALY_WINDOW_SIZE = int(os.getenv("ANOMALY_WINDOW_SIZE", 100))
ANOMALY_Z_THRESHOLD = float(os.getenv("ANOMALY_Z_THRESHOLD", 2.5))
ANOMALY_RATE_WINDOW_SECONDS = int(os.getenv("ANOMALY_RATE_WINDOW_SECONDS", 60))
ANOMALY_RATE_THRESHOLD_MULTIPLIER = float(os.getenv("ANOMALY_RATE_THRESHOLD_MULTIPLIER", 3.0))
ANOMALY_MIN_SAMPLES = int(os.getenv("ANOMALY_MIN_SAMPLES", 10))

# ── Forwarding (API mode) ──────────────────────────────────────────
FORWARD_URL = os.getenv("FORWARD_URL", "")