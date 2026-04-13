import threading
import time
from collections import defaultdict, deque


class IncidentMetrics:

    def __init__(self):
        self._lock = threading.RLock()
        self.start_time = time.time()

        self.signals_received = 0
        self.signals_correlated = 0
        self.incidents_created = 0
        self.incidents_updated = 0
        self.incidents_by_severity: dict[str, int] = defaultdict(int)
        self.incidents_by_status: dict[str, int] = defaultdict(int)

        self._rate_window: deque[float] = deque()
        self._rate_span = 10.0

    def record_signal_received(self):
        with self._lock:
            self.signals_received += 1
            self._rate_window.append(time.time())

    def record_signal_correlated(self):
        with self._lock:
            self.signals_correlated += 1

    def record_incident_created(self, severity: str):
        with self._lock:
            self.incidents_created += 1
            self.incidents_by_severity[severity] += 1

    def record_incident_updated(self):
        with self._lock:
            self.incidents_updated += 1

    def record_status_change(self, old_status: str, new_status: str):
        with self._lock:
            if old_status:
                self.incidents_by_status[old_status] = max(0, self.incidents_by_status.get(old_status, 1) - 1)
            self.incidents_by_status[new_status] = self.incidents_by_status.get(new_status, 0) + 1

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
                "signals_received": self.signals_received,
                "signals_correlated": self.signals_correlated,
                "incidents_created": self.incidents_created,
                "incidents_updated": self.incidents_updated,
                "signals_per_second": self.get_throughput(),
                "uptime_seconds": round(time.time() - self.start_time, 1),
                "incidents_by_severity": dict(self.incidents_by_severity),
                "incidents_by_status": dict(self.incidents_by_status),
            }


metrics = IncidentMetrics()
