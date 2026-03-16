import logging

from config import (
    CRITICAL_RISK_THRESHOLD,
    CRITICAL_SERVICES,
    CRITICAL_SIGNAL_COUNT,
    HIGH_SIGNAL_COUNT,
)

logger = logging.getLogger("incident.severity")

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


class SeverityEngine:

    def compute_initial_severity(self, signal: dict) -> str:
        signal_severity = signal.get("severity", "low").lower()
        risk_score = signal.get("risk_score", 0.0)
        service = signal.get("affected_service") or signal.get("service", "")

        severity = signal_severity

        if risk_score >= CRITICAL_RISK_THRESHOLD:
            severity = "critical"
        elif service in CRITICAL_SERVICES and SEVERITY_RANK.get(signal_severity, 0) >= 2:
            severity = self._escalate(signal_severity)

        logger.info(
            "Initial severity computed: %s (signal=%s, risk=%.2f, service=%s)",
            severity, signal_severity, risk_score, service,
        )
        return severity

    def recompute_severity(self, incident: dict) -> str:
        current = incident.get("severity", "low")
        signal_count = incident.get("signal_count", 1)
        risk_score = incident.get("risk_score", 0.0)
        service = incident.get("affected_service", "")

        severity = current

        if signal_count >= CRITICAL_SIGNAL_COUNT:
            severity = "critical"
        elif signal_count >= HIGH_SIGNAL_COUNT and SEVERITY_RANK.get(current, 0) < 3:
            severity = "high"

        if risk_score >= CRITICAL_RISK_THRESHOLD:
            severity = "critical"

        if service in CRITICAL_SERVICES and SEVERITY_RANK.get(severity, 0) < 3:
            severity = self._escalate(severity)

        if SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(current, 0):
            logger.info(
                "Incident escalated: %s -> %s (signals=%d, risk=%.2f)",
                current, severity, signal_count, risk_score,
                extra={"incident_id": incident.get("incident_id")},
            )

        return severity

    @staticmethod
    def _escalate(severity: str) -> str:
        mapping = {"info": "low", "low": "medium", "medium": "high", "high": "critical"}
        return mapping.get(severity, severity)
