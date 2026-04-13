import math
import threading

from config import (
    ML_RUNTIME_ANOMALY_Z_THRESHOLD,
    ML_RUNTIME_LEARN_ON_ANOMALY,
    ML_RUNTIME_MIN_STD,
    ML_RUNTIME_WARMUP_SAMPLES,
)

FEATURE_ORDER = [
    "failed_login_count",
    "request_rate",
    "error_ratio",
    "unique_ip_count",
    "endpoint_entropy",
    "time_of_day",
]


class _RunningStat:
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0

    def update(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.m2 += delta * delta2

    def std(self, min_std: float) -> float:
        if self.n < 2:
            return min_std
        variance = self.m2 / (self.n - 1)
        return max(math.sqrt(max(variance, 0.0)), min_std)


class RuntimeAnomalyModel:
    """Simple online z-score anomaly model trained incrementally at runtime."""

    def __init__(self):
        self._lock = threading.RLock()
        self._stats = {name: _RunningStat() for name in FEATURE_ORDER}
        self._total_samples = 0

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _vectorize(self, features: dict) -> dict[str, float]:
        return {name: self._to_float(features.get(name, 0.0)) for name in FEATURE_ORDER}

    @staticmethod
    def _score_from_z(avg_z: float) -> float:
        # Smoothly maps z distance to 0..1.
        return round(1.0 - math.exp(-avg_z / 3.0), 6)

    def predict(self, features: dict) -> dict:
        vector = self._vectorize(features)

        with self._lock:
            warm = self._total_samples >= ML_RUNTIME_WARMUP_SAMPLES
            z_scores: list[float] = []

            for name, value in vector.items():
                stat = self._stats[name]
                z = 0.0
                if stat.n >= 2:
                    z = abs((value - stat.mean) / stat.std(ML_RUNTIME_MIN_STD))
                z_scores.append(z)

            avg_z = sum(z_scores) / len(z_scores) if z_scores else 0.0
            anomaly_score = self._score_from_z(avg_z)
            is_anomaly = warm and (avg_z >= ML_RUNTIME_ANOMALY_Z_THRESHOLD)

            should_learn = (not is_anomaly) or ML_RUNTIME_LEARN_ON_ANOMALY
            if should_learn:
                for name, value in vector.items():
                    self._stats[name].update(value)
                self._total_samples += 1

            return {
                "is_anomaly": is_anomaly,
                "anomaly_score": anomaly_score,
                "ml_used": True,
                "error": None,
                "source": "runtime",
                "avg_z": round(avg_z, 6),
                "trained_samples": self._total_samples,
            }

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "trained_samples": self._total_samples,
                "warmup_samples": ML_RUNTIME_WARMUP_SAMPLES,
                "z_threshold": ML_RUNTIME_ANOMALY_Z_THRESHOLD,
            }
