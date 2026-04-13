from models.detection_signal import DetectionSignal
from rules.base_rule import BaseRule


class LatencyRule(BaseRule):
    """Fires HIGH_LATENCY when request latency exceeds a static threshold."""

    def __init__(self):
        self.threshold_ms = 2000

    def configure(self, rule_id: str, params: dict) -> None:
        super().configure(rule_id, params)
        self.threshold_ms = params.get("threshold_ms", self.threshold_ms)

    def check(self, event: dict) -> dict | None:
        if event.get("event_type") != "http.request":
            return None

        latency = event.get("metadata", {}).get("latency_ms", 0)

        if latency > self.threshold_ms:
            return DetectionSignal(
                signal_type="HIGH_LATENCY",
                severity="MEDIUM",
                service=event.get("service_name", "unknown"),
                metadata={"latency_ms": latency, "threshold_ms": self.threshold_ms},
                source="rule",
                rule_id=self.rule_id,
            ).to_dict()

        return None