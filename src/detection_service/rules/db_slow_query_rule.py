from models.detection_signal import DetectionSignal
from rules.base_rule import BaseRule


class DBSlowQueryRule(BaseRule):
    """Fires DB_SLOW_QUERY when database query latency exceeds threshold."""

    def __init__(self):
        self.threshold_ms = 3000

    def configure(self, rule_id: str, params: dict) -> None:
        super().configure(rule_id, params)
        self.threshold_ms = params.get("threshold_ms", self.threshold_ms)

    def check(self, event: dict) -> dict | None:
        if event.get("event_type") != "db.query":
            return None

        latency = event.get("metadata", {}).get("latency_ms", 0)

        if latency > self.threshold_ms:
            return DetectionSignal(
                signal_type="DB_SLOW_QUERY",
                severity="MEDIUM",
                service=event.get("service_name", "unknown"),
                metadata={"latency_ms": latency, "threshold_ms": self.threshold_ms},
                source="rule",
                rule_id=self.rule_id,
            ).to_dict()

        return None