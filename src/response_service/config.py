import os
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Redis Channels/Streams
INCIDENT_STREAM = os.getenv("INCIDENT_STREAM", "incident_events")
RESPONSE_STREAM = os.getenv("RESPONSE_STREAM", "response_events")
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
