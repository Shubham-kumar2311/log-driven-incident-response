import logging
from datetime import datetime, timezone, timedelta

from config import CORRELATION_WINDOW_SECONDS
from models.incident_model import build_correlation_key

logger = logging.getLogger("incident.correlation")


class CorrelationEngine:

    def __init__(self, store):
        self._store = store

    def find_matching_incident(self, signal: dict) -> dict | None:
        correlation_key = build_correlation_key(signal)
        cutoff = (
            datetime.now(timezone.utc) - timedelta(seconds=CORRELATION_WINDOW_SECONDS)
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        incident = self._store.find_open_by_correlation_key(correlation_key, cutoff)

        if incident:
            logger.info(
                "Signal correlated to existing incident",
                extra={
                    "signal_id": signal.get("signal_id"),
                    "incident_id": incident["incident_id"],
                },
            )

        return incident
