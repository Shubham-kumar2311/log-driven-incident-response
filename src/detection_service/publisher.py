import json
import logging

import redis
import requests

from config import FORWARD_URL, OUTPUT_STREAM, REDIS_HOST, REDIS_PORT, USE_REDIS

logger = logging.getLogger("detection.publisher")

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
    return _redis_client


def publish_signal(signal: dict) -> None:
    """Publish a detection signal to the configured output channel."""
    signal_type = signal.get("signal_type", "unknown")
    service = signal.get("service", "unknown")

    if USE_REDIS:
        try:
            _get_redis().xadd(OUTPUT_STREAM, {"data": json.dumps(signal)})
            logger.info(
                "Signal published to Redis stream",
                extra={"signal_type": signal_type, "service_name": service},
            )
        except redis.RedisError:
            logger.exception("Failed to publish signal to Redis")
    elif FORWARD_URL:
        try:
            resp = requests.post(FORWARD_URL, json={"signals": [signal]}, timeout=5)
            resp.raise_for_status()
            logger.info(
                "Signal forwarded via HTTP",
                extra={"signal_type": signal_type, "service_name": service},
            )
        except requests.RequestException:
            logger.exception("Failed to forward signal to %s", FORWARD_URL)
    else:
        logger.info(
            "Signal produced (no output sink configured)",
            extra={"signal_type": signal_type, "service_name": service},
        )


def publish_signals(signals: list[dict]) -> None:
    """Convenience: publish a batch of signals."""
    for signal in signals:
        publish_signal(signal)