import logging

logger = logging.getLogger("processing.features")


def _bucket(value, thresholds: list[tuple[float, str]], default: str = "LOW") -> str:
    for threshold, label in thresholds:
        if value > threshold:
            return label
    return default


LATENCY_BUCKETS = [(5000, "CRITICAL"), (1000, "HIGH"), (200, "MEDIUM")]
DURATION_BUCKETS = [(10000, "CRITICAL"), (5000, "HIGH"), (1000, "MEDIUM")]


class FeatureExtractor:
    """Extract detection-ready features from the event for the detection engine."""

    def process(self, event: dict) -> dict | None:
        features = {}
        metadata = event.get("metadata") or {}
        norm_type = event.get("normalized_type", "")

        # --- Latency bucket ---
        latency = metadata.get("latency_ms")
        if latency is None:
            latency = metadata.get("response_time_ms")
        if latency is not None:
            try:
                latency = float(latency)
                features["latency_ms"] = latency
                features["latency_bucket"] = _bucket(latency, LATENCY_BUCKETS)
            except (ValueError, TypeError):
                pass

        # --- Duration bucket (workers, db queries) ---
        duration = metadata.get("duration_ms")
        if duration is not None:
            try:
                duration = float(duration)
                features["duration_ms"] = duration
                features["duration_bucket"] = _bucket(duration, DURATION_BUCKETS)
            except (ValueError, TypeError):
                pass

        # --- HTTP status code ---
        status = metadata.get("status_code")
        if status is None:
            status = metadata.get("status")
        if status is not None:
            try:
                features["status_code"] = int(status)
                features["is_error_response"] = int(status) >= 400
            except (ValueError, TypeError):
                pass

        # --- Auth features ---
        if norm_type in ("AUTH_FAILURE", "AUTH_SUCCESS"):
            features["username"] = metadata.get("username", "unknown")
            features["client_ip"] = metadata.get("client_ip", "unknown")
            features["auth_method"] = metadata.get("method", "unknown")
            if metadata.get("reason"):
                features["failure_reason"] = metadata["reason"]

        # --- K8s features ---
        if norm_type.startswith("K8S_"):
            for key in ("pod", "namespace", "node", "restart_count", "reason"):
                if key in metadata:
                    features[f"k8s_{key}"] = metadata[key]

        # --- Deployment features ---
        if norm_type.startswith("DEPLOY_"):
            for key in ("version", "strategy", "target", "component"):
                if key in metadata:
                    features[f"deploy_{key}"] = metadata[key]

        # --- Worker features ---
        if norm_type.startswith("WORKER_"):
            if "job" in metadata:
                features["job_name"] = metadata["job"]
            if "retries" in metadata:
                features["retry_count"] = metadata["retries"]
            if "reason" in metadata:
                features["failure_reason"] = metadata["reason"]

        # --- DB features ---
        if norm_type.startswith("DB_"):
            if "query_type" in metadata:
                features["query_type"] = metadata["query_type"]
            if "table" in metadata:
                features["table"] = metadata["table"]

        features["service"] = event.get("service_name", "unknown")
        features["severity"] = event.get("severity", "LOW")

        event["features"] = features
        return event