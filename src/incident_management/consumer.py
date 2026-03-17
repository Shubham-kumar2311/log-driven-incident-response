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
from pipeline import IncidentPipeline

logger = logging.getLogger("incident.consumer")

BACKOFF_BASE = 1
BACKOFF_MAX = 30


class DetectionConsumer:

    def __init__(self):
        self.redis = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=False
        )
        self.pipeline = IncidentPipeline()
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
            "Incident consumer started (group=%s, name=%s, stream=%s)",
            CONSUMER_GROUP, CONSUMER_NAME, INPUT_STREAM,
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

                backoff = BACKOFF_BASE

                for stream, events in messages:
                    for msg_id, data in events:
                        try:
                            signal = json.loads(data[b"data"])
                            self.pipeline.process(signal)
                            self.redis.xack(INPUT_STREAM, CONSUMER_GROUP, msg_id)
                        except (json.JSONDecodeError, KeyError):
                            logger.warning("Malformed message %s, acknowledging and skipping", msg_id)
                            self.redis.xack(INPUT_STREAM, CONSUMER_GROUP, msg_id)
                        except Exception:
                            logger.exception("Error processing message %s", msg_id)

            except redis.ConnectionError:
                logger.error("Redis connection lost, retrying in %ds", backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
            except Exception:
                logger.exception("Unexpected error in consumer loop, retrying in %ds", backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
