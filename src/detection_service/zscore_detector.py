import math
import threading

from config import ANOMALY_MIN_SAMPLES, ANOMALY_Z_THRESHOLD


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

    def std(self) -> float:
        if self.n < 2:
            return 0.0
        variance = self.m2 / (self.n - 1)
        return math.sqrt(max(variance, 0.0))


class ZScoreDetector:
    """Online z-score detector for request/error behavior."""

    FEATURE_KEYS = ("request_rate", "error_ratio")

    def __init__(
        self,
        threshold: float = ANOMALY_Z_THRESHOLD,
        min_samples: int = ANOMALY_MIN_SAMPLES,
        min_std: float = 0.05,
    ):
        self.threshold = threshold
        self.min_samples = min_samples
        self.min_std = min_std
        self._stats = {k: _RunningStat() for k in self.FEATURE_KEYS}
        self._lock = threading.RLock()

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def evaluate(self, features: dict) -> dict:
        request_rate = self._to_float(features.get("request_rate"))
        error_ratio = self._to_float(features.get("error_ratio"))
        vector = {
            "request_rate": request_rate,
            "error_ratio": error_ratio,
        }

        with self._lock:
            z_scores = {}
            enough_history = True
            max_z = 0.0

            for key, value in vector.items():
                stat = self._stats[key]
                if stat.n < self.min_samples:
                    enough_history = False
                    z = 0.0
                else:
                    std = stat.std()
                    z = abs((value - stat.mean) / max(std, self.min_std))
                z_scores[key] = round(z, 6)
                max_z = max(max_z, z)

            is_anomaly = enough_history and (max_z >= self.threshold)

            # Learn online after evaluating to avoid contaminating the current score.
            for key, value in vector.items():
                self._stats[key].update(value)

            return {
                "is_anomaly": is_anomaly,
                "z_score": round(max_z, 6),
                "z_score_request_rate": z_scores["request_rate"],
                "z_score_error_ratio": z_scores["error_ratio"],
                "source": "zscore",
            }
