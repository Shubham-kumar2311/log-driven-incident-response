import json
import logging

import redis
import requests

from config import FORWARD_URL, OUTPUT_CHANNEL, REDIS_HOST, REDIS_PORT, USE_REDIS

logger = logging.getLogger("incident.publisher")

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return _redis_client


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
            resp = requests.post(FORWARD_URL, json=incident, timeout=5)
            resp.raise_for_status()
            logger.info("Incident forwarded via HTTP", extra={"incident_id": incident_id})
        except requests.RequestException:
            logger.exception("Failed to forward incident to %s", FORWARD_URL)
    else:
        logger.info("Incident produced (no output sink configured)", extra={"incident_id": incident_id})
