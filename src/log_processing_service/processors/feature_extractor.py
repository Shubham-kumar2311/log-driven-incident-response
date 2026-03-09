class FeatureExtractor:

    def process(self, event):

        features = {}

        latency = event["metadata"].get("latency_ms")

        if latency:

            if latency > 1000:
                features["latency_bucket"] = "HIGH"
            elif latency > 200:
                features["latency_bucket"] = "MEDIUM"
            else:
                features["latency_bucket"] = "LOW"

        features["service"] = event["service_name"]

        event["features"] = features

        return event