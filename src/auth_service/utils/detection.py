"""
Detection Integration
Send authentication events to detection service
"""
import httpx
import logging
from datetime import datetime
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


async def send_login_event(
    username: str,
    ip_address: str,
    success: bool,
    user_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    is_new_ip: bool = False,
    failed_attempts: int = 0
):
    """
    Send login event to detection service.
    Detection rules:
    - >5 failed logins in 2 minutes → brute force alert
    - login from new IP → anomaly alert
    """
    event = {
        "event_type": "auth.login",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "auth_service",
        "data": {
            "username": username,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": "SUCCESS" if success else "FAILED",
            "is_new_ip": is_new_ip,
            "recent_failed_attempts": failed_attempts
        },
        "tags": {
            "service": "auth",
            "action": "login"
        }
    }

    # Add threat indicators
    if failed_attempts >= settings.BRUTE_FORCE_THRESHOLD:
        event["threat_indicator"] = "brute_force_suspected"
        event["severity"] = "high"

    if is_new_ip and success:
        event["anomaly_indicator"] = "new_ip_login"
        event["severity"] = event.get("severity", "medium")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                settings.DETECTION_SERVICE_URL,
                json=event
            )
            if response.status_code == 200:
                logger.debug(f"Login event sent to detection service: {username}")
            else:
                logger.warning(f"Detection service returned {response.status_code}")
    except httpx.ConnectError:
        logger.debug("Detection service not available (connection refused)")
    except Exception as e:
        logger.warning(f"Failed to send event to detection service: {e}")


async def send_registration_event(
    username: str,
    email: str,
    ip_address: str,
    role: str
):
    """Send registration event to detection service"""
    event = {
        "event_type": "auth.registration",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "auth_service",
        "data": {
            "username": username,
            "email": email,
            "ip_address": ip_address,
            "role": role
        },
        "tags": {
            "service": "auth",
            "action": "registration"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(settings.DETECTION_SERVICE_URL, json=event)
    except Exception as e:
        logger.debug(f"Failed to send registration event: {e}")
