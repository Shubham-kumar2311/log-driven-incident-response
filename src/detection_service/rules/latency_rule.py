from models.detection_signal import DetectionSignal


class LatencyRule:

    def check(self, event):

        if event.get("event_type") != "http.request":
            return None

        latency = event.get("metadata", {}).get("latency_ms", 0)

        if latency > 2000:

            return DetectionSignal(
                "HIGH_LATENCY",
                "MEDIUM",
                event.get("service_name"),
                {"latency_ms": latency}
            ).to_dict()

        return None