"""
Central Auth Server Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""

    # Server
    APP_NAME = "Central Auth Server"
    HOST = os.getenv("AUTH_HOST", "0.0.0.0")
    PORT = int(os.getenv("AUTH_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "auth_db")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # Cookie
    COOKIE_NAME = "auth_token"
    COOKIE_MAX_AGE = 3600  # 1 hour in seconds
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_HTTPONLY = True
    COOKIE_SAMESITE = "lax"

    # CORS - Allow all UI ports
    CORS_ORIGINS = [
        "http://localhost:8001/",  # USER UI
        "http://localhost:8001",  # ANALYST UI
        "http://localhost:8001",  # ADMIN UI
        "http://localhost:8001",  # Auth server itself
    ]

    # Role-based redirects
    ROLE_REDIRECTS = {
        "USER": "http://localhost:8001",
        "ANALYST": "http://localhost:8001",
        "ADMIN": "http://localhost:8001"
    }

    # Detection Service
    DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://localhost:8003/detect")

    # Bcrypt
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

    # Brute Force Detection
    BRUTE_FORCE_THRESHOLD = 5
    BRUTE_FORCE_WINDOW_SECONDS = 120  # 2 minutes


settings = Settings()
