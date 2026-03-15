import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LOG_RATE_MIN = float(os.getenv("LOG_RATE_MIN", "0.2"))
LOG_RATE_MAX = float(os.getenv("LOG_RATE_MAX", "1.0"))
MODE = os.getenv("MODE", "normal")
OUTPUT_MODE = os.getenv("OUTPUT_MODE", "file")  # file | http | redis

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_env_log_dir = os.getenv("LOG_DIR", None)
if _env_log_dir:
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), _env_log_dir))
else:
    LOG_DIR = os.path.join(BASE_DIR, "logs")

HTTP_INGESTION_URL = os.getenv("HTTP_INGESTION_URL", "http://localhost:8001/logs")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_STREAM = os.getenv("REDIS_STREAM", "raw_logs")
