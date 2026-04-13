import time
from collections import defaultdict

from models.detection_signal import DetectionSignal
from rules.base_rule import BaseRule


class AuthFailureRule(BaseRule):
    """Fires BRUTE_FORCE_LOGIN when repeated login failures from same IP exceed threshold."""

    def __init__(self):
        self.failures: dict[str, list[float]] = defaultdict(list)
        self.threshold = 5
        self.window_seconds = 60

    def configure(self, rule_id: str, params: dict) -> None:
        super().configure(rule_id, params)
        self.threshold = params.get("threshold", self.threshold)
        self.window_seconds = params.get("window_seconds", self.window_seconds)

    def check(self, event: dict) -> dict | None:
        if event.get("event_type") != "auth.login_failed":
            return None

        ip = event.get("metadata", {}).get("client_ip")
        if not ip:
            return None

        now = time.time()
        self.failures[ip].append(now)

        # Expire old entries
        self.failures[ip] = [
            t for t in self.failures[ip]
            if now - t <= self.window_seconds
        ]

        if len(self.failures[ip]) >= self.threshold:
            self.failures[ip].clear()
            return DetectionSignal(
                signal_type="BRUTE_FORCE_LOGIN",
                severity="HIGH",
                service=event.get("service_name", "unknown"),
                metadata={"ip": ip, "threshold": self.threshold},
                source="rule",
                rule_id=self.rule_id,
            ).to_dict()

        return None