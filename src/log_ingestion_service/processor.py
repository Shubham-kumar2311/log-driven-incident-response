import uuid
import logging
from datetime import datetime, timezone
from models import LogEntry
from stats_tracker import stats

logger = logging.getLogger("ingestion.processor")


def process_log(raw: dict) -> dict:
    try:
        entry = LogEntry(**raw)
        normalized = entry.normalize()

        if not normalized.get("event_id"):
            normalized["event_id"] = str(uuid.uuid4())

        normalized["ingested_at"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        stats.record_log(normalized)
        return normalized

    except Exception as e:
        logger.error("Log processing failed: %s", e)
        stats.record_error()
        return None


def process_batch(logs: list) -> list:
    results = []
    for raw in logs:
        result = process_log(raw)
        if result:
            results.append(result)
    return results
