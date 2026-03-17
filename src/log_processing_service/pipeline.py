import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone

from processors.validator import Validator
from processors.normalizer import Normalizer
from processors.noise_filter import NoiseFilter
from processors.enricher import Enricher
from processors.feature_extractor import FeatureExtractor
from models.normalized_event import ProcessedEvent

logger = logging.getLogger("processing.pipeline")


class PipelineMetrics:
    """Thread-safe counters for pipeline observability."""

    def __init__(self):
        self._lock = threading.RLock()
        self.total_in = 0
        self.total_out = 0
        self.dropped = 0
        self.errors = 0
        self.start_time = time.time()
        self._rate_window: deque[float] = deque()

    def record_in(self):
        with self._lock:
            self.total_in += 1

    def record_out(self):
        now = time.time()
        with self._lock:
            self.total_out += 1
            self._rate_window.append(now)

    def record_drop(self):
        with self._lock:
            self.dropped += 1

    def record_error(self):
        with self._lock:
            self.errors += 1

    def get_rate(self) -> float:
        now = time.time()
        with self._lock:
            cutoff = now - 5.0
            while self._rate_window and self._rate_window[0] < cutoff:
                self._rate_window.popleft()
            count = len(self._rate_window)
        return round(count / 5.0, 2) if count else 0.0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "total_in": self.total_in,
                "total_out": self.total_out,
                "dropped": self.dropped,
                "errors": self.errors,
                "events_per_second": self.get_rate(),
                "uptime_seconds": round(time.time() - self.start_time, 1),
            }


class ProcessingPipeline:
    """
    Five-stage processing pipeline:
      1. Validator   - parse & resolve fields, drop malformed
      2. Normalizer  - classify event_type -> normalized_type + severity
      3. NoiseFilter - drop health checks, probes, debug logs
      4. Enricher    - add region, cluster, risk_score, tags
      5. FeatureExtractor - extract detection-ready features
    """

    def __init__(self):
        self.steps = [
            ("validator", Validator()),
            ("normalizer", Normalizer()),
            ("noise_filter", NoiseFilter()),
            ("enricher", Enricher()),
            ("feature_extractor", FeatureExtractor()),
        ]
        self.metrics = PipelineMetrics()

    def process(self, event: dict) -> dict | None:
        self.metrics.record_in()

        for step_name, step in self.steps:
            try:
                event = step.process(event)
                if event is None:
                    self.metrics.record_drop()
                    logger.debug("Event dropped at stage: %s", step_name)
                    return None
            except Exception as e:
                self.metrics.record_error()
                logger.error("Pipeline error at %s: %s", step_name, e)
                return None

        # Add processed_at timestamp
        event["processed_at"] = datetime.now(timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")

        # Validate output schema
        try:
            processed = ProcessedEvent(**event)
            result = processed.model_dump()
        except Exception as e:
            self.metrics.record_error()
            logger.error("Output validation failed: %s", e)
            return None

        self.metrics.record_out()
        return result

    def process_batch(self, events: list[dict]) -> list[dict]:
        results = []
        for event in events:
            result = self.process(event)
            if result:
                results.append(result)
        return results

    def get_metrics(self) -> dict:
        return self.metrics.snapshot()
