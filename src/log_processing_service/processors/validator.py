import logging
import uuid
from datetime import datetime, timezone

from models.raw_event import RawEvent

logger = logging.getLogger("processing.validator")

REQUIRED_RESOLVED = ["service_name", "log_level", "event_type"]


class Validator:
    """Parse raw dict into RawEvent, resolve dual fields, ensure required fields present."""

    def process(self, event: dict) -> dict | None:
        try:
            raw = RawEvent(**event)
        except Exception as e:
            logger.warning("Validation parse error: %s", e)
            return None

        resolved = {
            "event_id": raw.event_id or str(uuid.uuid4()),
            "timestamp": raw.timestamp or datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "service_name": raw.resolved_service(),
            "category": raw.category,
            "log_level": raw.resolved_level(),
            "event_type": raw.resolved_event_type(),
            "message": raw.message,
            "trace_id": raw.trace_id,
            "span_id": raw.span_id,
            "host": raw.host,
            "container_id": raw.container_id,
            "environment": raw.environment or "production",
            "schema_version": raw.schema_version or "1.0",
            "metadata": raw.metadata or {},
            "ingested_at": raw.ingested_at,
        }

        for field in REQUIRED_RESOLVED:
            if not resolved.get(field) or resolved[field] == "unknown":
                logger.debug("Dropping event: missing %s", field)
                return None

        return resolved