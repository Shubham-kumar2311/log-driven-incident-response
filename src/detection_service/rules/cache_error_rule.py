import time
from collections import deque

from models.detection_signal import DetectionSignal
from rules.base_rule import BaseRule


class CacheErrorRule(BaseRule):
    """Fires CACHE_CONNECTION_ERROR when cache-related errors exceed threshold in a sliding window."""

    def __init__(self):
        self.window: deque[float] = deque()
        self.threshold = 5
        self.window_seconds = 60

    def configure(self, rule_id: str, params: dict) -> None:
        super().configure(rule_id, params)
        self.threshold = params.get("threshold", self.threshold)
        self.window_seconds = params.get("window_seconds", self.window_seconds)

    def check(self, event: dict) -> dict | None:
        event_type = event.get("event_type", "")
        normalized = event.get("normalized_type", "")
        message = (event.get("message") or "").lower()
        severity = event.get("severity", "")

        is_cache_event = (
            "cache" in event_type.lower()
            or "CACHE" in normalized
            or ("cache" in message and any(kw in message for kw in ("error", "fail", "timeout", "refused", "unreachable")))
            or ("redis" in message and any(kw in message for kw in ("error", "fail", "timeout", "connection")))
        )

        if not is_cache_event:
            return None

        # Only count actual errors, not normal cache operations
        if severity in ("INFO",) and "error" not in message and "fail" not in message:
            return None

        now = time.time()
        self.window.append(now)

        while self.window and now - self.window[0] > self.window_seconds:
            self.window.popleft()

        if len(self.window) >= self.threshold:
            count = len(self.window)
            self.window.clear()
            return DetectionSignal(
                signal_type="CACHE_CONNECTION_ERROR",
                severity="HIGH",
                service=event.get("service_name", "unknown"),
                metadata={"count": count, "window_seconds": self.window_seconds},
                source="rule",
                rule_id=self.rule_id,
            ).to_dict()

        return None
