import json
import logging
import queue

from config import (
    USE_REDIS, REDIS_HOST, REDIS_PORT,
    OUTPUT_STREAM, MAX_QUEUE_SIZE,
)

logger = logging.getLogger("processing.publisher")

_redis_client = None
_local_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)


def _get_redis():
    global _redis_client
    if _redis_client is None and USE_REDIS:
        import redis
        _redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
    return _redis_client


def publish_event(event: dict) -> bool:
    """Publish a processed event to the detection service.

    Redis mode:  xadd to OUTPUT_STREAM (processed_logs)
    Local mode:  push onto in-memory queue for API consumption
    """
    if USE_REDIS:
        return _publish_redis(event)
    return _publish_local(event)


def _publish_redis(event: dict) -> bool:
    try:
        client = _get_redis()
        if client:
            client.xadd(OUTPUT_STREAM, {"data": json.dumps(event)})
            return True
    except Exception as e:
        logger.error("Redis publish failed: %s", e)
    # Fallback to local queue so /processed endpoint still works
    return _publish_local(event)


def _publish_local(event: dict) -> bool:
    try:
        _local_queue.put_nowait(event)
        return True
    except queue.Full:
        logger.warning("Local processed queue full (%d), dropping event", MAX_QUEUE_SIZE)
        return False


def get_local_queue() -> queue.Queue:
    """Expose the local queue for the API layer."""
    return _local_queue
