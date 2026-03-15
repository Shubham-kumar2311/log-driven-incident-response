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
    ):
        self.signal_id = str(uuid.uuid4())
        self.signal_type = signal_type
        self.severity = severity
        self.service = service
        self.metadata = metadata
        self.source = source
        self.confidence = round(min(max(confidence, 0.0), 1.0), 3)
        self.rule_id = rule_id
        self.detected_at = datetime.now(timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "severity": self.severity,
            "service": self.service,
            "metadata": self.metadata,
            "source": self.source,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            "detected_at": self.detected_at,
        }