"""
Redis Stream Publisher for Actuator Service.

Publishes execution results to the actuator_events stream.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import redis

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0].rsplit("\\", 2)[0])
from config import (
    USE_REDIS,
    REDIS_HOST,
    REDIS_PORT,
    ACTUATOR_STREAM,
)

logger = logging.getLogger(__name__)


class ActuatorPublisher:
    """Publisher for actuator execution events to Redis Stream."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
        return self._client

    def publish(self, execution_result: Dict[str, Any]) -> Optional[str]:
        """
        Publish an execution result to Redis Stream.

        Args:
            execution_result: Execution result data to publish

        Returns:
            Message ID if published, None if Redis is disabled
        """
        if not USE_REDIS:
            logger.debug("Redis disabled, skipping publish")
            return None

        try:
            client = self._get_client()

            # Add metadata
            event = {
                **execution_result,
                "published_at": datetime.now(timezone.utc).isoformat()
            }

            # Serialize the result
            message = {
                "data": json.dumps(event),
                "type": "actuator_event",
                "action": execution_result.get("action", "unknown"),
                "status": execution_result.get("execution_status", "unknown")
            }

            # Add to stream
            message_id = client.xadd(
                ACTUATOR_STREAM,
                message,
                maxlen=10000  # Keep last 10k messages
            )

            logger.info(
                f"Published to '{ACTUATOR_STREAM}': {message_id} "
                f"(action={execution_result.get('action')}, "
                f"status={execution_result.get('execution_status')})"
            )
            return message_id

        except redis.ConnectionError as e:
            logger.error(f"Failed to publish to Redis: {e}")
            return None
        except Exception as e:
            logger.error(f"Error publishing execution result: {e}", exc_info=True)
            return None

    def publish_batch(self, results: list) -> list:
        """
        Publish multiple execution results.

        Args:
            results: List of execution results

        Returns:
            List of message IDs (None for failed publishes)
        """
        return [self.publish(result) for result in results]

    def close(self):
        """Close the Redis connection."""
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


# Global publisher instance
publisher = ActuatorPublisher()


def publish_event(execution_result: Dict[str, Any]) -> Optional[str]:
    """Convenience function to publish an execution result."""
    return publisher.publish(execution_result)
