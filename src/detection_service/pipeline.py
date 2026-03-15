import logging

from anomaly_engine import AnomalyEngine
from metrics import metrics
from rule_engine import RuleEngine

logger = logging.getLogger("detection.pipeline")


class DetectionPipeline:
    """
    Full detection pipeline:
      event -> rule_engine -> anomaly_engine -> combined signals
    """

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.anomaly_engine = AnomalyEngine()
        logger.info("Detection pipeline initialized")

    def process(self, event: dict) -> list[dict]:
        metrics.record_event_processed()

        # Stage 1: Rule-based detection
        rule_signals = self.rule_engine.evaluate(event)
        rule_types = {s.get("signal_type") for s in rule_signals}

        for sig in rule_signals:
            metrics.record_rule_signal(sig.get("rule_id", "unknown"))

        # Stage 2: Anomaly-based detection
        anomaly_signals = self.anomaly_engine.evaluate(event)

        for sig in anomaly_signals:
            # If a rule already caught a related issue, mark as corroborated
            if sig.get("signal_type", "").replace("_ANOMALY", "") in {
                t.replace("_SPIKE", "").replace("HIGH_", "") for t in rule_types
            }:
                sig["metadata"]["corroborated"] = True

            metrics.record_anomaly_signal(sig.get("rule_id", "unknown"))

        all_signals = rule_signals + anomaly_signals

        if all_signals:
            logger.info(
                "Detection complete: %d rule signals, %d anomaly signals",
                len(rule_signals),
                len(anomaly_signals),
                extra={"event_id": event.get("event_id")},
            )

        return all_signals

    def process_batch(self, events: list[dict]) -> list[dict]:
        all_signals: list[dict] = []
        for event in events:
            all_signals.extend(self.process(event))
        return all_signals