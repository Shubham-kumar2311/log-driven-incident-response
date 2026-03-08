from collections import deque
import time

from models.detection_signal import DetectionSignal


class HTTPErrorRule:

    def __init__(self):

        self.window = deque()
        self.threshold = 10
        self.window_seconds = 30

    def check(self, event):

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

            self.window.clear()

            return DetectionSignal(
                "HTTP_ERROR_SPIKE",
                "HIGH",
                event.get("service_name"),
                {"count": self.threshold}
            ).to_dict()

        return None