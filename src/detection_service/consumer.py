import json
import logging
import time

import redis

from config import (
    CONSUMER_GROUP,
    CONSUMER_NAME,
    INPUT_STREAM,
    REDIS_HOST,
    REDIS_PORT,
)
from metrics import metrics
from pipeline import DetectionPipeline
from publisher import publish_signals

logger = logging.getLogger("detection.consumer")

BACKOFF_BASE = 1
BACKOFF_MAX = 30


class DetectionConsumer:
    """Consumes processed events from a Redis Stream using consumer groups."""

    def __init__(self):
        self.redis = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=False
        )
        self.pipeline = DetectionPipeline()
        self._ensure_consumer_group()

    def _ensure_consumer_group(self) -> None:
        try:
            self.redis.xgroup_create(INPUT_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
            logger.info("Created consumer group '%s' on stream '%s'", CONSUMER_GROUP, INPUT_STREAM)
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info("Consumer group '%s' already exists", CONSUMER_GROUP)
            else:
                raise

    def run(self) -> None:
        logger.info(
            "Detection consumer started (group=%s, name=%s)",
            CONSUMER_GROUP,
            CONSUMER_NAME,
        )
        backoff = BACKOFF_BASE

        while True:
            try:
                messages = self.redis.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {INPUT_STREAM: ">"},
                    count=50,
                    block=5000,
                )

                if not messages:
                    continue

                backoff = BACKOFF_BASE  # reset on success

                for stream, events in messages:
                    for msg_id, data in events:
                        try:
                            event = json.loads(data[b"data"])
                            signals = self.pipeline.process(event)

                            if signals:
                                publish_signals(signals)

                            # ACK after successful processing
                            self.redis.xack(INPUT_STREAM, CONSUMER_GROUP, msg_id)
                        except (json.JSONDecodeError, KeyError):
                            logger.warning("Malformed message %s, acknowledging and skipping", msg_id)
                            self.redis.xack(INPUT_STREAM, CONSUMER_GROUP, msg_id)
                            metrics.record_event_error()
                        except Exception:
                            logger.exception("Error processing message %s", msg_id)
                            metrics.record_event_error()

            except redis.ConnectionError:
                logger.error("Redis connection lost, retrying in %ds", backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
            except Exception:
                logger.exception("Unexpected error in consumer loop, retrying in %ds", backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)