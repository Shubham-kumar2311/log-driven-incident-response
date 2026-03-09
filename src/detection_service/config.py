import os
from dotenv import load_dotenv

load_dotenv()

USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

INPUT_STREAM = "processed_logs"
OUTPUT_STREAM = "detection_signals"