import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8016"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

CORS_ORIGINS = _csv_env(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8016",
)

PROCESSING_SERVICE_URL = os.getenv("PROCESSING_SERVICE_URL", "http://localhost:8002")
DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://localhost:8003")
INCIDENT_SERVICE_URL = os.getenv("INCIDENT_SERVICE_URL", "http://localhost:8004")
RESPONSE_SERVICE_URL = os.getenv("RESPONSE_SERVICE_URL", "http://localhost:8005")
ACTUATOR_SERVICE_URL = os.getenv("ACTUATOR_SERVICE_URL", "http://localhost:8007")
PIPELINE_DEMO_TIMEOUT_SECONDS = float(os.getenv("PIPELINE_DEMO_TIMEOUT_SECONDS", "20"))
