import math
from datetime import datetime


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_hour(timestamp: str | None) -> int:
    if not timestamp:
        return 0

    normalized = timestamp.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).hour
    except ValueError:
        return 0


def _endpoint_entropy(path: str) -> float:
    if not path:
        return 0.0

    counts: dict[str, int] = {}
    for ch in path:
        counts[ch] = counts.get(ch, 0) + 1

    length = len(path)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)

    return round(entropy, 6)


class FeatureExtractor:
    """Converts a normalized log event into ML model input features."""

    @staticmethod
    def extract(event: dict) -> dict:
        metadata = event.get("metadata") or {}
        features = event.get("features") or {}

        status = metadata.get("status")
        if status is None:
            status = features.get("status_code")

        is_error = 0
        if status is not None:
            is_error = 1 if _to_int(status, 0) >= 400 else 0

        failed_login_count = metadata.get("failed_login_count")
        if failed_login_count is None and event.get("event_type") == "auth.login_failed":
            failed_login_count = 1

        unique_ip_count = metadata.get("unique_ip_count")
        if unique_ip_count is None:
            unique_ip_count = 1 if metadata.get("client_ip") else 0

        path = metadata.get("path") or metadata.get("endpoint") or ""

        return {
            "failed_login_count": _to_int(failed_login_count, 0),
            "request_rate": _to_float(metadata.get("request_rate", features.get("request_rate", 1.0)), 1.0),
            "error_ratio": _to_float(metadata.get("error_ratio", is_error), 0.0),
            "unique_ip_count": _to_int(unique_ip_count, 0),
            "endpoint_entropy": _to_float(metadata.get("endpoint_entropy", _endpoint_entropy(path)), 0.0),
            "time_of_day": _safe_hour(event.get("timestamp")),
            "z_score_request_rate": _to_float(metadata.get("z_score_request_rate", 0.0), 0.0),
            "z_score_error_ratio": _to_float(metadata.get("z_score_error_ratio", 0.0), 0.0),
        }
