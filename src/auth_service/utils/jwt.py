"""
JWT Utility
Token generation and verification
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt

from config import settings


def create_token(user_id: str, role: str) -> str:
    """
    Create JWT token with user_id and role.
    Expiry: 1 hour (configurable)
    """
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
        "iss": "auth-server"
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.
    Returns payload if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verification (for debugging)"""
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False}
        )
    except Exception:
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get token expiry time"""
    payload = decode_token_unsafe(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None
