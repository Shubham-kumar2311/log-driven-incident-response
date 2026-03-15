import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_env_log_dir = os.getenv("LOG_DIR", None)
if _env_log_dir:
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), _env_log_dir))
else:
    LOG_DIR = os.path.join(BASE_DIR, "logs")

_env_offset = os.getenv("OFFSET_FILE", "offsets.json")
OFFSET_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), _env_offset))

POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "1.0"))

USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_STREAM = os.getenv("REDIS_STREAM", "raw_logs")

PROCESS_API = os.getenv("PROCESS_API", "http://localhost:8002/process")

MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "10000"))

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))
