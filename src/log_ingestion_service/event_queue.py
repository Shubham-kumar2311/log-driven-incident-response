import queue
import logging

from config import MAX_QUEUE_SIZE

logger = logging.getLogger("ingestion.queue")

_publish_queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)


def enqueue(event: dict) -> bool:
    """Non-blocking enqueue. Returns False if queue is full (backpressure)."""
    try:
        _publish_queue.put_nowait(event)
        return True
    except queue.Full:
        logger.warning("Publish queue full (%d), dropping event", MAX_QUEUE_SIZE)
        return False


def get_queue() -> queue.Queue:
    return _publish_queue
