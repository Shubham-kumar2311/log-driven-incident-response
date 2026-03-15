import json
import logging
import time
import requests

from config import USE_REDIS, REDIS_HOST, REDIS_PORT, REDIS_STREAM, PROCESS_API

logger = logging.getLogger("ingestion.publisher")

_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None and USE_REDIS:
        import redis
        _redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
    return _redis_client


def publish_event(event: dict):
    for attempt in range(3):
        try:
            if USE_REDIS:
                import redis as redis_mod
                client = _get_redis_client()
                if client:
                    client.xadd(REDIS_STREAM, {"data": json.dumps(event)})
                    return True
            else:
                resp = requests.post(PROCESS_API, json=event, timeout=3)
                if resp.status_code < 300:
                    return True
                logger.warning("Process API returned %d", resp.status_code)
        except requests.RequestException as e:
            logger.warning("Publish attempt %d failed: %s", attempt + 1, e)
            time.sleep(0.3 * (attempt + 1))
        except Exception as e:
            logger.warning("Publish attempt %d failed: %s", attempt + 1, e)
            time.sleep(0.3 * (attempt + 1))

    logger.error("Failed to publish event after 3 attempts")
    return False


def publish_batch(events: list) -> int:
    success = 0
    for event in events:
        if publish_event(event):
            success += 1
    return success
