import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
OFFSET_FILE = os.getenv("OFFSET_FILE", "offsets.json")

POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", 1.0))

USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

PROCESS_API = os.getenv("PROCESS_API", "http://localhost:8002/process")