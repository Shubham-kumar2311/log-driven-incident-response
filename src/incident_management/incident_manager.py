import logging

from correlation_engine import CorrelationEngine
from incident_store import IncidentStore
from metrics import metrics
from models.incident_model import new_incident, _now
from severity_engine import SeverityEngine

logger = logging.getLogger("incident.manager")


class IncidentManager:

    def __init__(self):
        self.store = IncidentStore()
        self.correlation = CorrelationEngine(self.store)
        self.severity = SeverityEngine()

    def process_signal(self, signal: dict) -> dict:
        metrics.record_signal_received()

        existing = self.correlation.find_matching_incident(signal)

        if existing:
            return self._update_incident(existing, signal)

        return self._create_incident(signal)

    def _create_incident(self, signal: dict) -> dict:
        severity = self.severity.compute_initial_severity(signal)
        incident = new_incident(
            affected_service=signal.get("affected_service") or signal.get("service", "unknown"),
            environment=signal.get("environment", "unknown"),
            region=signal.get("region", "unknown"),
            severity=severity,
            signal=signal,
        )

        self.store.save_incident(incident)
        metrics.record_incident_created(severity)
        metrics.record_status_change("", "open")

        logger.info(
            "New incident created",
            extra={
                "incident_id": incident["incident_id"],
                "severity": severity,
                "affected_service": incident["affected_service"],
            },
        )
        return incident

    def _update_incident(self, incident: dict, signal: dict) -> dict:
        incident_id = incident["incident_id"]

        updated = self.store.add_signal_to_incident(incident_id, signal)
        metrics.record_signal_correlated()
        metrics.record_incident_updated()

        new_severity = self.severity.recompute_severity(updated)
        if new_severity != updated.get("severity"):
            self.store.update_severity(incident_id, new_severity)
            updated = self.store.get_incident(incident_id)

        logger.info(
            "Incident updated with new signal",
            extra={
                "incident_id": incident_id,
                "signal_id": signal.get("signal_id"),
                "signal_count": updated.get("signal_count"),
            },
        )
        return updated

    def process_signals_batch(self, signals: list[dict]) -> list[dict]:
        results = []
        for signal in signals:
            result = self.process_signal(signal)
            results.append(result)
        return results
