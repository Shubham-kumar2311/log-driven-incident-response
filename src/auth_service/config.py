"""
Central Auth Server Configuration
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _csv_env(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """Application settings"""

    # Server
    APP_NAME = "Central Auth Server"
    HOST = os.getenv("AUTH_HOST", os.getenv("HOST", "0.0.0.0"))
    PORT = int(os.getenv("AUTH_PORT", os.getenv("PORT", "3000")))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "auth_db")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # Cookie
    COOKIE_NAME = os.getenv("COOKIE_NAME", "auth_token")
    COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", "3600"))
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_HTTPONLY = os.getenv("COOKIE_HTTPONLY", "true").lower() == "true"
    COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

    # CORS
    CORS_ORIGINS = _csv_env(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8001,http://localhost:8004,http://localhost:8005,http://localhost:8006,http://localhost:8007",
    )

    # Role-based redirects
    ROLE_REDIRECTS = {
        "USER": os.getenv("ROLE_REDIRECT_USER", "http://localhost:8001"),
        "ANALYST": os.getenv("ROLE_REDIRECT_ANALYST", "http://localhost:8004"),
        "ADMIN": os.getenv("ROLE_REDIRECT_ADMIN", "http://localhost:8005"),
    }

    # Detection Service
    DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://localhost:8003/detect")

    # Bcrypt
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Brute Force Detection
    BRUTE_FORCE_THRESHOLD = int(os.getenv("BRUTE_FORCE_THRESHOLD", "5"))
    BRUTE_FORCE_WINDOW_SECONDS = int(os.getenv("BRUTE_FORCE_WINDOW_SECONDS", "120"))


settings = Settings()
