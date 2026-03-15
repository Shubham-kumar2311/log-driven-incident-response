import uuid
from datetime import datetime, timezone


class DetectionSignal:

    def __init__(
        self,
        signal_type: str,
        severity: str,
        service: str,
        metadata: dict,
        source: str = "rule",
        confidence: float = 1.0,
        rule_id: str = "",
        event_id: str = "",
        event_type: str = "",
        affected_service: str = "",
        environment: str = "",
        region: str = "",
        risk_score: float = 0.0,
    ):
        self.signal_id = str(uuid.uuid4())
        self.event_id = event_id
        self.event_type = event_type
        self.signal_type = signal_type
        self.severity = severity
        self.service = service
        self.affected_service = affected_service
        self.environment = environment
        self.region = region
        self.risk_score = risk_score
        self.source = source
        self.confidence = round(min(max(confidence, 0.0), 1.0), 3)
        self.rule_id = rule_id
        self.detected_at = datetime.now(timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "signal_type": self.signal_type,
            "severity": self.severity,
            "service": self.service,
            "affected_service": self.affected_service,
            "environment": self.environment,
            "region": self.region,
            "risk_score": self.risk_score,
            "source": self.source,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            "detected_at": self.detected_at,
            "metadata": self.metadata,
        }