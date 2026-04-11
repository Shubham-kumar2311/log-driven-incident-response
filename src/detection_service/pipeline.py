import logging

from decision_engine import DecisionEngine
from detection_store import DetectionStore
from feature_extractor import FeatureExtractor
from metrics import metrics
from ml_client import MLClient
from models.detection_signal import DetectionSignal
from rule_engine import RuleEngine
from zscore_detector import ZScoreDetector
from config import RUN_ML_WHEN_RULE_TRIGGERED, SKIP_ML_IF_RULE_TRIGGERED

logger = logging.getLogger("detection.pipeline")


class DetectionPipeline:
    """
    Hybrid detection pipeline:
    event -> rule_engine + zscore_detector + ML -> decision_engine -> final signal
    """

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.ml_client = MLClient()
        self.feature_extractor = FeatureExtractor()
        self.zscore_detector = ZScoreDetector()
        self.decision_engine = DecisionEngine()
        self.store = DetectionStore()
        logger.info("Detection pipeline initialized")

    def process(self, event: dict) -> list[dict]:
        metrics.record_event_processed()

        # Stage 1: Rule-based detection (primary layer)
        rule_signals = self.rule_engine.evaluate(event)
        rule_triggered = len(rule_signals) > 0

        for sig in rule_signals:
            metrics.record_rule_signal(sig.get("rule_id", "unknown"))

        # Stage 2: Statistical z-score detection.
        ml_features = self.feature_extractor.extract(event)
        zscore_result = self.zscore_detector.evaluate(ml_features)
        ml_features["z_score_request_rate"] = zscore_result.get("z_score_request_rate", 0.0)
        ml_features["z_score_error_ratio"] = zscore_result.get("z_score_error_ratio", 0.0)

        # Stage 3: ML anomaly detection (external isolation forest by default).
        ml_result: dict | None = None
        should_run_ml = True
        if rule_triggered and SKIP_ML_IF_RULE_TRIGGERED and not RUN_ML_WHEN_RULE_TRIGGERED:
            should_run_ml = False

        if should_run_ml:
            ml_result = self.ml_client.predict(ml_features)

        decision = self.decision_engine.combine(rule_signals, zscore_result, ml_result)

        if decision["ml_triggered"]:
            metrics.record_anomaly_signal((ml_result or {}).get("source", "ml"))
        if decision["zscore_triggered"]:
            metrics.record_anomaly_signal("zscore")

        self.store.save_detection_result(
            {
                "log_id": event.get("event_id", ""),
                "rule_triggered": decision["rule_triggered"],
                "rule_type": decision.get("rule_type"),
                "zscore_triggered": decision["zscore_triggered"],
                "z_score": decision.get("z_score"),
                "z_score_request_rate": decision.get("z_score_request_rate"),
                "z_score_error_ratio": decision.get("z_score_error_ratio"),
                "ml_triggered": decision["ml_triggered"],
                "ml_score": decision.get("anomaly_score"),
                "severity": decision["severity"],
                "source": decision["detection_source"],
                "timestamp": event.get("processed_at") or event.get("timestamp"),
                "features": ml_features,
            }
        )

        if decision["severity"] == "NORMAL":
            return []

        signal = DetectionSignal(
            signal_type="HYBRID_ANOMALY",
            severity=decision["severity"],
            service=event.get("service_name", "unknown"),
            source=decision["detection_source"],
            confidence=1.0 if decision["severity"] == "CRITICAL" else 0.85,
            rule_id=decision.get("rule_type") or "",
            event_id=event.get("event_id", ""),
            event_type=event.get("event_type", ""),
            affected_service=event.get("service_name", ""),
            environment=event.get("environment", ""),
            region=event.get("region", ""),
            risk_score=event.get("risk_score", 0.0),
            metadata={
                "detection_source": decision["source"],
                "detection_components": decision["detection_source"],
                "rule_type": decision.get("rule_type"),
                "anomaly_score": decision.get("anomaly_score"),
                "ml_score": decision.get("anomaly_score"),
                "z_score": decision.get("z_score"),
                "z_score_request_rate": decision.get("z_score_request_rate"),
                "z_score_error_ratio": decision.get("z_score_error_ratio"),
                "ml_used": decision.get("ml_used", False),
                "ml_error": decision.get("ml_error"),
                "ml_source": (ml_result or {}).get("source"),
                "original_log": event,
                "features": ml_features,
            },
        ).to_dict()

        logger.info(
            "Hybrid detection decision made",
            extra={
                "event_id": event.get("event_id"),
                "severity": decision["severity"],
                "source": decision["detection_source"],
            },
        )

        return [signal]

    def process_batch(self, events: list[dict]) -> list[dict]:
        all_signals: list[dict] = []
        for event in events:
            all_signals.extend(self.process(event))
        return all_signals