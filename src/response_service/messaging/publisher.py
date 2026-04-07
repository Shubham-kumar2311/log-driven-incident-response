import json
import logging
from typing import Dict, Any, Optional
import redis

from config import USE_REDIS, REDIS_HOST, REDIS_PORT, RESPONSE_STREAM

logger = logging.getLogger(__name__)


class ResponsePublisher:
    """Publisher for response events to Redis Stream."""

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

    def publish(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Publish a response event to Redis Stream.

        Args:
            response: Response data to publish

        Returns:
            Message ID if published, None if Redis is disabled
        """
        if not USE_REDIS:
            logger.debug("Redis disabled, skipping publish")
            return None

        try:
            client = self._get_client()

            # Serialize the response
            message = {
                "data": json.dumps(response),
                "type": "response_event"
            }

            # Add to stream
            message_id = client.xadd(
                RESPONSE_STREAM,
                message,
                maxlen=10000  # Keep last 10k messages
            )

            logger.info(f"Published response to '{RESPONSE_STREAM}': {message_id}")
            return message_id

        except redis.ConnectionError as e:
            logger.error(f"Failed to publish to Redis: {e}")
            return None
        except Exception as e:
            logger.error(f"Error publishing response: {e}", exc_info=True)
            return None

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
publisher = ResponsePublisher()


def publish_response(response: Dict[str, Any]) -> Optional[str]:
    """Convenience function to publish a response."""
    return publisher.publish(response)
