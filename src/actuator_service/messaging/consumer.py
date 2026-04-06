"""
Redis Stream Consumer for Actuator Service.

Consumes response events from the Response Service and triggers action execution.
"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional
import redis

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0].rsplit("\\", 2)[0])
from config import (
    USE_REDIS,
    REDIS_HOST,
    REDIS_PORT,
    RESPONSE_STREAM,
    CONSUMER_GROUP,
    CONSUMER_NAME,
)

logger = logging.getLogger(__name__)


class ResponseConsumer:
    """
    Redis Stream consumer for response events.

    Consumes from 'response_events' stream and processes actions.
    Uses consumer groups for at-least-once delivery semantics.
    """

    def __init__(
        self,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
        batch_size: int = 10,
        block_ms: int = 5000
    ):
        self._client: Optional[redis.Redis] = None
        self._on_event = on_event
        self._batch_size = batch_size
        self._block_ms = block_ms
        self._running = False
        self._retry_delay = 1.0
        self._max_retry_delay = 30.0

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
        """Create consumer group if it doesn't exist."""
        client = self._get_client()
        try:
            client.xgroup_create(
                RESPONSE_STREAM,
                CONSUMER_GROUP,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group '{CONSUMER_GROUP}' on '{RESPONSE_STREAM}'")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{CONSUMER_GROUP}' already exists")
            else:
                raise

    def set_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Set the event handler callback."""
        self._on_event = handler

    async def start(self):
        """Start consuming events from Redis Stream."""
        if not USE_REDIS:
            logger.info("Redis disabled (USE_REDIS=false), consumer not started")
            return

        self._running = True
        retry_delay = self._retry_delay

        while self._running:
            try:
                client = self._get_client()
                self._ensure_consumer_group()

                logger.info(
                    f"Consumer started: stream={RESPONSE_STREAM}, "
                    f"group={CONSUMER_GROUP}, consumer={CONSUMER_NAME}"
                )

                # Reset retry delay on successful connection
                retry_delay = self._retry_delay

                # Process pending messages first (unacknowledged)
                await self._process_pending()

                # Main consumption loop
                while self._running:
                    try:
                        messages = client.xreadgroup(
                            groupname=CONSUMER_GROUP,
                            consumername=CONSUMER_NAME,
                            streams={RESPONSE_STREAM: ">"},
                            count=self._batch_size,
                            block=self._block_ms
                        )

                        if messages:
                            for stream_name, stream_messages in messages:
                                for message_id, fields in stream_messages:
                                    await self._process_message(message_id, fields)

                    except redis.ConnectionError:
                        raise  # Re-raise to trigger reconnection
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        await asyncio.sleep(1)

            except redis.ConnectionError as e:
                logger.warning(f"Redis connection error: {e}")
                self._client = None

                if self._running:
                    logger.info(f"Reconnecting in {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self._max_retry_delay)

            except Exception as e:
                logger.error(f"Consumer error: {e}", exc_info=True)
                if self._running:
                    await asyncio.sleep(retry_delay)

    async def _process_pending(self):
        """Process any pending (unacknowledged) messages."""
        client = self._get_client()

        try:
            pending = client.xpending(RESPONSE_STREAM, CONSUMER_GROUP)
            if pending and pending.get("pending", 0) > 0:
                logger.info(f"Processing {pending['pending']} pending messages")

                # Claim and process pending messages
                messages = client.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={RESPONSE_STREAM: "0"},
                    count=pending["pending"]
                )

                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            await self._process_message(message_id, fields)

        except Exception as e:
            logger.warning(f"Error processing pending messages: {e}")

    async def _process_message(self, message_id: str, fields: Dict[str, str]):
        """Process a single message from the stream."""
        try:
            # Parse the message data
            data_str = fields.get("data", "{}")
            data = json.loads(data_str)

            logger.debug(f"Processing message {message_id}: type={fields.get('type')}")

            # Call the event handler
            if self._on_event:
                await self._invoke_handler(data)

            # Acknowledge the message
            client = self._get_client()
            client.xack(RESPONSE_STREAM, CONSUMER_GROUP, message_id)
            logger.debug(f"Acknowledged message {message_id}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message {message_id}: {e}")
            # ACK invalid messages to prevent reprocessing
            client = self._get_client()
            client.xack(RESPONSE_STREAM, CONSUMER_GROUP, message_id)
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
            # Don't ACK on processing errors - will be retried

    async def _invoke_handler(self, data: Dict[str, Any]):
        """Invoke the event handler, handling both sync and async handlers."""
        if self._on_event is None:
            return

        if asyncio.iscoroutinefunction(self._on_event):
            await self._on_event(data)
        else:
            self._on_event(data)

    def stop(self):
        """Stop the consumer."""
        logger.info("Stopping consumer...")
        self._running = False

    def close(self):
        """Close the Redis connection."""
        self.stop()
        if self._client:
            self._client.close()
            self._client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not USE_REDIS:
            return False
        try:
            client = self._get_client()
            client.ping()
            return True
        except Exception:
            return False


# Global consumer instance
consumer = ResponseConsumer()
