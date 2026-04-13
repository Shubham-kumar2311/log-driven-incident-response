import time
from collections import deque

from models.detection_signal import DetectionSignal
from rules.base_rule import BaseRule


class HTTPErrorRule(BaseRule):
    """Fires HTTP_ERROR_SPIKE when HTTP 500+ errors exceed threshold in a sliding window."""

    def __init__(self):
        self.window: deque[float] = deque()
        self.threshold = 10
        self.window_seconds = 30

    def configure(self, rule_id: str, params: dict) -> None:
        super().configure(rule_id, params)
        self.threshold = params.get("threshold", self.threshold)
        self.window_seconds = params.get("window_seconds", self.window_seconds)

    def check(self, event: dict) -> dict | None:
        if event.get("event_type") != "http.request":
            return None

        status = event.get("metadata", {}).get("status")
        if status is None or status < 500:
            return None

        now = time.time()
        self.window.append(now)

        while self.window and now - self.window[0] > self.window_seconds:
            self.window.popleft()

        if len(self.window) >= self.threshold:
            count = len(self.window)
            self.window.clear()
            return DetectionSignal(
                signal_type="HTTP_ERROR_SPIKE",
                severity="HIGH",
                service=event.get("service_name", "unknown"),
                metadata={"count": count, "window_seconds": self.window_seconds},
                source="rule",
                rule_id=self.rule_id,
            ).to_dict()

        return None