import logging
from config import NOISE_EVENT_TYPES, NOISE_SERVICES

logger = logging.getLogger("processing.noise_filter")


class NoiseFilter:
    """Drop events that match noisy patterns (health checks, probes, etc.)."""

    def process(self, event: dict) -> dict | None:
        event_type = event.get("event_type", "")
        service = event.get("service_name", "")

        if event_type in NOISE_EVENT_TYPES:
            logger.debug("Noise drop: event_type=%s", event_type)
            return None

        if service in NOISE_SERVICES:
            logger.debug("Noise drop: service=%s", service)
            return None

        # Drop DEBUG-level logs in production
        if event.get("log_level") == "DEBUG" and event.get("environment", "production") == "production":
            return None

        return event
