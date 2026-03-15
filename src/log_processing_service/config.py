import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- Redis ---
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
INPUT_STREAM = os.getenv("INPUT_STREAM", "raw_logs")
OUTPUT_STREAM = os.getenv("OUTPUT_STREAM", "processed_logs")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "processing-group")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "processor-1")

# --- API ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8002"))

# --- Processing ---
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "0.1"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "10000"))

# --- Noise filter ---
NOISE_EVENT_TYPES = set(os.getenv(
    "NOISE_EVENT_TYPES",
    "http.health_check,k8s.probe"
).split(","))
NOISE_SERVICES = set(os.getenv("NOISE_SERVICES", "").split(",")) - {""}

# --- Enrichment ---
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "us-east-1")
DEFAULT_CLUSTER = os.getenv("DEFAULT_CLUSTER", "prod-cluster")
DEFAULT_ENVIRONMENT = os.getenv("DEFAULT_ENVIRONMENT", "production")

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")