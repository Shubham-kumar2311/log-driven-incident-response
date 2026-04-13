import time
import threading
import logging
from collections import deque

logger = logging.getLogger("ingestion.stats")


class StatsTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self.total_logs = 0
        self.error_count = 0
        self.services = set()
        self.start_time = time.time()
        self._recent_logs = deque(maxlen=50)
        self._rate_window = deque(maxlen=300)

    def record_log(self, normalized: dict):
        now = time.time()
        with self._lock:
            self.total_logs += 1
            self._rate_window.append(now)
            svc = normalized.get("service_name") or normalized.get("service", "unknown")
            self.services.add(svc)
            self._recent_logs.append(normalized)

    def record_error(self):
        with self._lock:
            self.error_count += 1

    def get_logs_per_second(self) -> float:
        now = time.time()
        with self._lock:
            cutoff = now - 5.0
            while self._rate_window and self._rate_window[0] < cutoff:
                self._rate_window.popleft()
            count = len(self._rate_window)
        return round(count / 5.0, 2) if count else 0.0

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "total_logs": self.total_logs,
                "logs_per_second": self.get_logs_per_second(),
                "services": sorted(self.services),
                "error_count": self.error_count,
                "uptime_seconds": round(time.time() - self.start_time, 1),
            }

    def get_recent_logs(self, limit: int = 20) -> list:
        with self._lock:
            logs = list(self._recent_logs)
        return logs[-limit:]


stats = StatsTracker()
