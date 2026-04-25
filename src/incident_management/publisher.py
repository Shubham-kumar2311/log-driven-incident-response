import json
import logging

import redis
import requests

from config import FORWARD_TIMEOUT_SECONDS, FORWARD_URL, OUTPUT_CHANNEL, REDIS_HOST, REDIS_PORT, USE_REDIS

logger = logging.getLogger("incident.publisher")

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return _redis_client


def _resolve_signal_type_from_incident(incident: dict) -> str | None:
    signal_type = incident.get("signal_type")
    if isinstance(signal_type, str) and signal_type.strip():
        return signal_type.strip()

    tags = incident.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and tag.startswith("rule:"):
                candidate = tag.split(":", 1)[1].strip()
                if candidate:
                    return candidate

    return None


def _to_response_payload(incident: dict) -> dict:
    incident_id = incident.get("incident_id", "unknown")
    signal_type = _resolve_signal_type_from_incident(incident)

    payload = {
        "id": incident_id,
        "incident_id": incident_id,
        "signal_type": signal_type,
        "error": signal_type,
        "service": incident.get("affected_service"),
        "details": {
            "source_incident": incident,
            "incident_id": incident_id,
        },
    }

    return {k: v for k, v in payload.items() if v is not None}


def publish_incident(incident: dict) -> None:
    incident_id = incident.get("incident_id", "unknown")

    if USE_REDIS:
        try:
            _get_redis().publish(OUTPUT_CHANNEL, json.dumps(incident, default=str))
            logger.info("Incident published to Redis channel", extra={"incident_id": incident_id})
        except redis.RedisError:
            logger.exception("Failed to publish incident to Redis")
    elif FORWARD_URL:
        try:
            response_payload = _to_response_payload(incident)
            resp = requests.post(FORWARD_URL, json=response_payload, timeout=FORWARD_TIMEOUT_SECONDS)
            resp.raise_for_status()
            logger.info("Incident forwarded via HTTP", extra={"incident_id": incident_id})
        except requests.RequestException:
            logger.exception("Failed to forward incident to %s", FORWARD_URL)
    else:
        logger.info("Incident produced (no output sink configured)", extra={"incident_id": incident_id})
