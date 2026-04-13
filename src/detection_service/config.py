import os
from pathlib import Path

from dotenv import load_dotenv

_service_dir = Path(__file__).resolve().parent
load_dotenv(_service_dir / ".env")

# ── Redis ───────────────────────────────────────────────────────────
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# ── Streams ─────────────────────────────────────────────────────────
INPUT_STREAM = os.getenv("INPUT_STREAM", "processed_logs")
OUTPUT_STREAM = os.getenv("OUTPUT_STREAM", "detection_signals")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "detection-group")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "detector-1")

# ── Service API ──────────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8003"))

# ── Rulebook ────────────────────────────────────────────────────────
RULEBOOK_PATH = os.getenv("RULEBOOK_PATH", str(_service_dir / "rulebook.json"))

# ── Hybrid Detection / External ML ─────────────────────────────────
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:9000/predict")
ML_REQUEST_TIMEOUT_SECONDS = float(os.getenv("ML_REQUEST_TIMEOUT_SECONDS", 2.5))
ML_MAX_RETRIES = int(os.getenv("ML_MAX_RETRIES", 1))
SKIP_ML_IF_RULE_TRIGGERED = os.getenv("SKIP_ML_IF_RULE_TRIGGERED", "false").lower() == "true"
RUN_ML_WHEN_RULE_TRIGGERED = os.getenv("RUN_ML_WHEN_RULE_TRIGGERED", "true").lower() == "true"
ML_MODE = os.getenv("ML_MODE", "external").lower()  # runtime | external | hybrid
ML_RUNTIME_WARMUP_SAMPLES = int(os.getenv("ML_RUNTIME_WARMUP_SAMPLES", 25))
ML_RUNTIME_ANOMALY_Z_THRESHOLD = float(os.getenv("ML_RUNTIME_ANOMALY_Z_THRESHOLD", 3.0))
ML_RUNTIME_MIN_STD = float(os.getenv("ML_RUNTIME_MIN_STD", 0.05))
ML_RUNTIME_LEARN_ON_ANOMALY = os.getenv("ML_RUNTIME_LEARN_ON_ANOMALY", "false").lower() == "true"

# ── Logging ─────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Statistical Detector Settings ───────────────────────────────────
ANOMALY_Z_THRESHOLD = float(os.getenv("ANOMALY_Z_THRESHOLD", 2.5))
ANOMALY_MIN_SAMPLES = int(os.getenv("ANOMALY_MIN_SAMPLES", 10))

# ── Forwarding (API mode) ──────────────────────────────────────────
FORWARD_URL = os.getenv("FORWARD_URL", "")

# ── MongoDB (Detection results + feedback) ─────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "detection_service")
USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
DETECTION_STORE_FILE = os.getenv("DETECTION_STORE_FILE", str(_service_dir / "detection_store.jsonl"))