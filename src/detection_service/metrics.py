import threading
import time
from collections import defaultdict, deque


class DetectionMetrics:
    """Thread-safe metrics collector for detection pipeline observability."""

    def __init__(self):
        self._lock = threading.RLock()
        self.start_time = time.time()

        # Global counters
        self.events_processed = 0
        self.events_errors = 0
        self.rule_signals_total = 0
        self.anomaly_signals_total = 0

        # Per-rule / per-detector hit counts
        self.rule_hits: dict[str, int] = defaultdict(int)
        self.anomaly_hits: dict[str, int] = defaultdict(int)

        # Throughput tracking (sliding window)
        self._rate_window: deque[float] = deque()
        self._rate_span = 10.0  # seconds

    # ── Recording ───────────────────────────────────────────────────

    def record_event_processed(self):
        with self._lock:
            self.events_processed += 1
            self._rate_window.append(time.time())

    def record_event_error(self):
        with self._lock:
            self.events_errors += 1

    def record_rule_signal(self, rule_id: str):
        with self._lock:
            self.rule_signals_total += 1
            self.rule_hits[rule_id] += 1

    def record_anomaly_signal(self, detector: str):
        with self._lock:
            self.anomaly_signals_total += 1
            self.anomaly_hits[detector] += 1

    # ── Reading ─────────────────────────────────────────────────────

    def get_throughput(self) -> float:
        now = time.time()
        with self._lock:
            cutoff = now - self._rate_span
            while self._rate_window and self._rate_window[0] < cutoff:
                self._rate_window.popleft()
            count = len(self._rate_window)
        return round(count / self._rate_span, 2) if count else 0.0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "events_processed": self.events_processed,
                "events_errors": self.events_errors,
                "rule_signals_total": self.rule_signals_total,
                "anomaly_signals_total": self.anomaly_signals_total,
                "signals_total": self.rule_signals_total + self.anomaly_signals_total,
                "events_per_second": self.get_throughput(),
                "uptime_seconds": round(time.time() - self.start_time, 1),
                "rule_hits": dict(self.rule_hits),
                "anomaly_hits": dict(self.anomaly_hits),
            }


# Singleton instance shared across modules
metrics = DetectionMetrics()
