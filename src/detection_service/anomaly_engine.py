import logging
import math
import time
from collections import defaultdict, deque

from config import (
    ANOMALY_MIN_SAMPLES,
    ANOMALY_RATE_THRESHOLD_MULTIPLIER,
    ANOMALY_RATE_WINDOW_SECONDS,
    ANOMALY_WINDOW_SIZE,
    ANOMALY_Z_THRESHOLD,
)
from models.detection_signal import DetectionSignal

logger = logging.getLogger("detection.anomaly_engine")


# ─── Helpers ────────────────────────────────────────────────────────

def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _stddev(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def _z_score(value: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return (value - mean) / std


def _confidence_from_z(z: float, threshold: float) -> float:
    """Map z-score to a 0-1 confidence. At threshold -> ~0.5, grows toward 1.0."""
    if z <= 0:
        return 0.0
    ratio = z / threshold
    return round(min(ratio / 2.0, 1.0), 3)


# ─── Error Rate Spike Detector ──────────────────────────────────────

class ErrorRateSpikeDetector:
    """
    Maintains a per-service sliding time-window of error events.
    Computes rolling error rate across fixed-size buckets and fires
    ERROR_RATE_ANOMALY when the current bucket's rate exceeds
    baseline_mean + z_threshold * stddev.
    """

    BUCKET_SECONDS = 10

    def __init__(
        self,
        window_seconds: int = ANOMALY_RATE_WINDOW_SECONDS,
        z_threshold: float = ANOMALY_Z_THRESHOLD,
        min_samples: int = ANOMALY_MIN_SAMPLES,
    ):
        self.window_seconds = window_seconds
        self.z_threshold = z_threshold
        self.min_samples = min_samples

        # service -> deque of (bucket_start_ts, count)
        self._buckets: dict[str, deque[tuple[float, int]]] = defaultdict(deque)
        # service -> current bucket accumulator
        self._current: dict[str, tuple[float, int]] = {}

    def _get_bucket_start(self, ts: float) -> float:
        return ts - (ts % self.BUCKET_SECONDS)

    def evaluate(self, event: dict) -> dict | None:
        severity = event.get("severity", "")
        if severity not in ("HIGH", "CRITICAL"):
            return None

        service = event.get("service_name", "unknown")
        now = time.time()
        bucket_start = self._get_bucket_start(now)

        # Roll current bucket
        cur = self._current.get(service)
        if cur is None or cur[0] != bucket_start:
            if cur is not None:
                self._buckets[service].append(cur)
            self._current[service] = (bucket_start, 0)

        self._current[service] = (bucket_start, self._current[service][1] + 1)

        # Expire old buckets
        cutoff = now - self.window_seconds
        buckets = self._buckets[service]
        while buckets and buckets[0][0] < cutoff:
            buckets.popleft()

        # Need enough history
        if len(buckets) < self.min_samples:
            return None

        rates = [c for _, c in buckets]
        mean = _mean(rates)
        std = _stddev(rates, mean)
        current_rate = self._current[service][1]
        z = _z_score(current_rate, mean, std)

        if z >= self.z_threshold:
            confidence = _confidence_from_z(z, self.z_threshold)
            logger.info(
                "Error rate anomaly detected",
                extra={"service_name": service, "detector": "error_rate_spike"},
            )
            return DetectionSignal(
                signal_type="ERROR_RATE_ANOMALY",
                severity="HIGH",
                service=service,
                metadata={
                    "current_rate": current_rate,
                    "baseline_mean": round(mean, 2),
                    "baseline_stddev": round(std, 2),
                    "z_score": round(z, 2),
                    "bucket_seconds": self.BUCKET_SECONDS,
                },
                source="anomaly",
                confidence=confidence,
                rule_id="error_rate_spike",
            ).to_dict()

        return None


# ─── Latency Anomaly Detector ───────────────────────────────────────

class LatencyAnomalyDetector:
    """
    Maintains a per-service sliding window of recent latency values.
    Fires LATENCY_ANOMALY when a new latency is z_threshold standard
    deviations above the rolling mean (z-score outlier detection).
    """

    def __init__(
        self,
        window_size: int = ANOMALY_WINDOW_SIZE,
        z_threshold: float = ANOMALY_Z_THRESHOLD,
        min_samples: int = ANOMALY_MIN_SAMPLES,
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.min_samples = min_samples
        # service -> deque of latency floats
        self._windows: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

    def evaluate(self, event: dict) -> dict | None:
        latency = event.get("metadata", {}).get("latency_ms")
        if latency is None:
            latency = event.get("features", {}).get("latency_ms")
        if latency is None:
            return None

        latency = float(latency)
        service = event.get("service_name", "unknown")
        window = self._windows[service]

        # Need baseline before detecting
        if len(window) >= self.min_samples:
            values = list(window)
            mean = _mean(values)
            std = _stddev(values, mean)
            z = _z_score(latency, mean, std)

            if z >= self.z_threshold:
                confidence = _confidence_from_z(z, self.z_threshold)
                window.append(latency)
                logger.info(
                    "Latency anomaly detected",
                    extra={
                        "service_name": service,
                        "latency_ms": latency,
                        "detector": "latency_anomaly",
                    },
                )
                return DetectionSignal(
                    signal_type="LATENCY_ANOMALY",
                    severity="MEDIUM",
                    service=service,
                    metadata={
                        "latency_ms": latency,
                        "baseline_mean": round(mean, 2),
                        "baseline_stddev": round(std, 2),
                        "z_score": round(z, 2),
                        "window_size": len(values),
                    },
                    source="anomaly",
                    confidence=confidence,
                    rule_id="latency_anomaly",
                ).to_dict()

        window.append(latency)
        return None


# ─── Event Frequency Anomaly Detector ───────────────────────────────

class FrequencyAnomalyDetector:
    """
    Tracks per-service event counts in fixed time-buckets.
    Fires FREQUENCY_ANOMALY when the current bucket rate exceeds
    baseline_mean * rate_multiplier.
    """

    BUCKET_SECONDS = 10

    def __init__(
        self,
        window_seconds: int = ANOMALY_RATE_WINDOW_SECONDS,
        rate_multiplier: float = ANOMALY_RATE_THRESHOLD_MULTIPLIER,
        min_samples: int = ANOMALY_MIN_SAMPLES,
    ):
        self.window_seconds = window_seconds
        self.rate_multiplier = rate_multiplier
        self.min_samples = min_samples

        self._buckets: dict[str, deque[tuple[float, int]]] = defaultdict(deque)
        self._current: dict[str, tuple[float, int]] = {}

    def _get_bucket_start(self, ts: float) -> float:
        return ts - (ts % self.BUCKET_SECONDS)

    def evaluate(self, event: dict) -> dict | None:
        service = event.get("service_name", "unknown")
        now = time.time()
        bucket_start = self._get_bucket_start(now)

        cur = self._current.get(service)
        if cur is None or cur[0] != bucket_start:
            if cur is not None:
                self._buckets[service].append(cur)
            self._current[service] = (bucket_start, 0)

        self._current[service] = (bucket_start, self._current[service][1] + 1)

        # Expire old buckets
        cutoff = now - self.window_seconds
        buckets = self._buckets[service]
        while buckets and buckets[0][0] < cutoff:
            buckets.popleft()

        if len(buckets) < self.min_samples:
            return None

        rates = [c for _, c in buckets]
        mean = _mean(rates)
        current_rate = self._current[service][1]
        threshold = mean * self.rate_multiplier

        if current_rate > threshold and mean > 0:
            ratio = current_rate / mean
            confidence = round(min((ratio - 1) / (self.rate_multiplier * 2), 1.0), 3)
            logger.info(
                "Frequency anomaly detected",
                extra={"service_name": service, "detector": "frequency_anomaly"},
            )
            return DetectionSignal(
                signal_type="FREQUENCY_ANOMALY",
                severity="MEDIUM",
                service=service,
                metadata={
                    "current_rate": current_rate,
                    "baseline_mean": round(mean, 2),
                    "threshold": round(threshold, 2),
                    "multiplier": self.rate_multiplier,
                    "bucket_seconds": self.BUCKET_SECONDS,
                },
                source="anomaly",
                confidence=confidence,
                rule_id="frequency_anomaly",
            ).to_dict()

        return None


# ─── Anomaly Engine (facade) ────────────────────────────────────────

class AnomalyEngine:
    """Runs all anomaly detectors against each event and returns signals."""

    def __init__(self):
        self.detectors = [
            ErrorRateSpikeDetector(),
            LatencyAnomalyDetector(),
            FrequencyAnomalyDetector(),
        ]
        logger.info("Anomaly engine ready — %d detectors loaded", len(self.detectors))

    def evaluate(self, event: dict) -> list[dict]:
        signals: list[dict] = []
        for detector in self.detectors:
            try:
                signal = detector.evaluate(event)
                if signal:
                    signals.append(signal)
            except Exception:
                logger.exception(
                    "Anomaly detector %s raised an exception",
                    type(detector).__name__,
                )
        return signals
