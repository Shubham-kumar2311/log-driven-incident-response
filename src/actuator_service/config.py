"""
Actuator Service Configuration
Environment-based configuration for execution modes and Redis connectivity.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Redis Streams
RESPONSE_STREAM = os.getenv("RESPONSE_STREAM", "response_events")
ACTUATOR_STREAM = os.getenv("ACTUATOR_STREAM", "actuator_events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "actuator_service_group")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "actuator_worker_1")

# Execution Configuration
USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", 30))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", 1.0))

# Docker Container Names (when USE_DOCKER=true)
DOCKER_DB_CONTAINER = os.getenv("DOCKER_DB_CONTAINER", "db-container")
DOCKER_API_CONTAINER = os.getenv("DOCKER_API_CONTAINER", "api-container")
DOCKER_CACHE_CONTAINER = os.getenv("DOCKER_CACHE_CONTAINER", "cache-container")
DOCKER_WORKER_CONTAINER = os.getenv("DOCKER_WORKER_CONTAINER", "worker-container")

# Service API URLs (for service-call mode)
SERVICE_API_BASE = os.getenv("SERVICE_API_BASE", "http://localhost:8080")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8081")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8082")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Execution History
MAX_HISTORY_SIZE = int(os.getenv("MAX_HISTORY_SIZE", 100))
