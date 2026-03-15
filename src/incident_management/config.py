import os
from dotenv import load_dotenv

load_dotenv()

USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

INCIDENT_HASH = "incidents"