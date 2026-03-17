import json
import logging
import time

from config import (
    USE_REDIS, REDIS_HOST, REDIS_PORT,
    INPUT_STREAM, CONSUMER_GROUP, CONSUMER_NAME,
    POLL_INTERVAL, BATCH_SIZE,
)
from pipeline import ProcessingPipeline
from publisher import publish_event

logger = logging.getLogger("processing.consumer")


class ProcessingConsumer:
    """Reads raw events from Redis Stream (consumer group) and runs them through the pipeline."""

    def __init__(self, pipeline: ProcessingPipeline | None = None):
        self.pipeline = pipeline or ProcessingPipeline()
        self._running = False
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            import redis
            self._redis = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
            )
            try:
                self._redis.xgroup_create(INPUT_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
                logger.info("Created consumer group '%s' on stream '%s'", CONSUMER_GROUP, INPUT_STREAM)
            except Exception:
                pass  # Group already exists
        return self._redis

    def run(self):
        if not USE_REDIS:
            logger.info("Redis disabled — consumer not starting")
            return

        self._running = True
        client = self._get_redis()
        logger.info(
            "Consumer started: group=%s, name=%s, stream=%s",
            CONSUMER_GROUP, CONSUMER_NAME, INPUT_STREAM,
        )

        while self._running:
            try:
                messages = client.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {INPUT_STREAM: ">"},
                    count=BATCH_SIZE,
                    block=int(POLL_INTERVAL * 1000) or 100,
                )

                if not messages:
                    continue

                for stream_name, entries in messages:
                    for msg_id, data in entries:
                        self._handle_message(client, msg_id, data)

            except Exception as e:
                logger.error("Consumer loop error: %s", e)
                time.sleep(1)

    def _handle_message(self, client, msg_id: str, data: dict):
        try:
            raw_json = data.get("data", "{}")
            event = json.loads(raw_json)
            processed = self.pipeline.process(event)

            if processed:
                publish_event(processed)

            # Acknowledge regardless (don't re-process drops)
            client.xack(INPUT_STREAM, CONSUMER_GROUP, msg_id)

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in message %s: %s", msg_id, e)
            client.xack(INPUT_STREAM, CONSUMER_GROUP, msg_id)
        except Exception as e:
            logger.error("Error processing message %s: %s", msg_id, e)

    def stop(self):
        self._running = False
        logger.info("Consumer stop requested")
