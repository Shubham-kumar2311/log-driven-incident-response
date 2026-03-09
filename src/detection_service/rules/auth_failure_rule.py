from collections import defaultdict
import time

from models.detection_signal import DetectionSignal


class AuthFailureRule:

    def __init__(self):

        self.failures = defaultdict(list)
        self.threshold = 5
        self.window_seconds = 60

    def check(self, event):

        if event.get("event_type") != "auth.login_failed":
            return None

        ip = event.get("metadata", {}).get("client_ip")

        if not ip:
            return None

        now = time.time()

        self.failures[ip].append(now)

        # remove old failures
        self.failures[ip] = [
            t for t in self.failures[ip]
            if now - t <= self.window_seconds
        ]

        if len(self.failures[ip]) >= self.threshold:

            self.failures[ip].clear()

            return DetectionSignal(
                "BRUTE_FORCE_LOGIN",
                "HIGH",
                event.get("service_name"),
                {"ip": ip}
            ).to_dict()

        return None