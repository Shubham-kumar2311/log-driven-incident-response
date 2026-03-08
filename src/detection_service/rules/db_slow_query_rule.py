from models.detection_signal import DetectionSignal


class DBSlowQueryRule:

    def check(self, event):

        if event.get("event_type") != "db.query":
            return None

        latency = event.get("metadata", {}).get("latency_ms", 0)

        if latency > 3000:

            return DetectionSignal(
                "DB_SLOW_QUERY",
                "MEDIUM",
                event.get("service_name"),
                {"latency_ms": latency}
            ).to_dict()

        return None