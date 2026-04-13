import json
import logging
import asyncio
from typing import Optional
import redis

from config import (
    USE_REDIS, REDIS_HOST, REDIS_PORT,
    INCIDENT_STREAM, CONSUMER_GROUP, CONSUMER_NAME
)

logger = logging.getLogger(__name__)


class IncidentConsumer:
    """Redis Stream consumer for incident events."""

    def __init__(self, callback):
        """
        Initialize the consumer.

        Args:
            callback: Async function to call with each incident
        """
        self.callback = callback
        self._client: Optional[redis.Redis] = None
        self._running = False
        self._backoff_seconds = 1
        self._max_backoff = 60

    def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
        return self._client

    def _ensure_consumer_group(self):
        """Ensure consumer group exists."""
        client = self._get_client()
        try:
            client.xgroup_create(
                INCIDENT_STREAM,
                CONSUMER_GROUP,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group '{CONSUMER_GROUP}' on stream '{INCIDENT_STREAM}'")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{CONSUMER_GROUP}' already exists")
            else:
                raise

    async def start(self):
        """Start consuming incidents from Redis Stream."""
        if not USE_REDIS:
            logger.info("Redis disabled (USE_REDIS=false), consumer not starting")
            return

        logger.info(f"Starting incident consumer on stream '{INCIDENT_STREAM}'")
        self._running = True
        self._ensure_consumer_group()

        while self._running:
            try:
                await self._consume_batch()
                self._backoff_seconds = 1  # Reset backoff on success
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                await self._backoff()
            except Exception as e:
                logger.error(f"Consumer error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _consume_batch(self):
        """Consume a batch of messages."""
        client = self._get_client()

        # Read from stream with consumer groups
        messages = client.xreadgroup(
            groupname=CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            streams={INCIDENT_STREAM: ">"},
            count=10,
            block=5000  # Block for 5 seconds
        )

        if not messages:
            return

        for stream_name, stream_messages in messages:
            for message_id, data in stream_messages:
                try:
                    await self._process_message(message_id, data)
                    # Acknowledge successful processing
                    client.xack(INCIDENT_STREAM, CONSUMER_GROUP, message_id)
                except Exception as e:
                    logger.error(f"Error processing message {message_id}: {e}")
                    # Don't ACK - message will be redelivered

    async def _process_message(self, message_id: str, data: dict):
        """Process a single message."""
        logger.debug(f"Processing message {message_id}: {data}")

        # Parse incident data
        if "data" in data:
            incident = json.loads(data["data"])
        else:
            incident = data

        # Call the callback
        await self.callback(incident)

    async def _backoff(self):
        """Exponential backoff on connection failure."""
        logger.warning(f"Backing off for {self._backoff_seconds}s")
        await asyncio.sleep(self._backoff_seconds)
        self._backoff_seconds = min(self._backoff_seconds * 2, self._max_backoff)

    def stop(self):
        """Stop the consumer."""
        logger.info("Stopping incident consumer")
        self._running = False
        if self._client:
            self._client.close()
            self._client = None

    async def process_pending(self):
        """Process any pending (unacknowledged) messages."""
        if not USE_REDIS:
            return

        client = self._get_client()
        self._ensure_consumer_group()

        # Check for pending messages
        pending = client.xpending(INCIDENT_STREAM, CONSUMER_GROUP)

        if pending and pending["pending"] > 0:
            logger.info(f"Found {pending['pending']} pending messages")

            # Claim and process pending messages
            messages = client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={INCIDENT_STREAM: "0"},  # Read pending
                count=100
            )

            for stream_name, stream_messages in messages:
                for message_id, data in stream_messages:
                    if data:  # Skip if data is empty (already processed)
                        try:
                            await self._process_message(message_id, data)
                            client.xack(INCIDENT_STREAM, CONSUMER_GROUP, message_id)
                        except Exception as e:
                            logger.error(f"Error processing pending message {message_id}: {e}")
