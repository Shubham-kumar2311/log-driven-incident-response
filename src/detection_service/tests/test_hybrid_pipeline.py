import unittest

from decision_engine import DecisionEngine
from pipeline import DetectionPipeline


class DecisionEngineTests(unittest.TestCase):
    def test_rule_and_ml_trigger_results_in_critical(self):
        decision = DecisionEngine.combine(
            rule_signals=[{"signal_type": "HTTP_ERROR_SPIKE", "rule_id": "http_error_spike"}],
            zscore_result={"is_anomaly": False, "z_score": 0.1},
            ml_result={"is_anomaly": True, "anomaly_score": 0.93, "ml_used": True},
        )
        self.assertEqual(decision["severity"], "CRITICAL")
        self.assertEqual(decision["source"], "combined")

    def test_rule_only_results_in_high(self):
        decision = DecisionEngine.combine(
            rule_signals=[{"signal_type": "BRUTE_FORCE_LOGIN", "rule_id": "auth_failures"}],
            zscore_result={"is_anomaly": False, "z_score": 0.1},
            ml_result={"is_anomaly": False, "anomaly_score": 0.1, "ml_used": True},
        )
        self.assertEqual(decision["severity"], "HIGH")
        self.assertEqual(decision["source"], "rule")

    def test_ml_only_results_in_medium(self):
        decision = DecisionEngine.combine(
            rule_signals=[],
            zscore_result={"is_anomaly": False, "z_score": 0.1},
            ml_result={"is_anomaly": True, "anomaly_score": 0.81, "ml_used": True},
        )
        self.assertEqual(decision["severity"], "MEDIUM")
        self.assertEqual(decision["source"], "ml")

    def test_zscore_and_ml_results_in_high(self):
        decision = DecisionEngine.combine(
            rule_signals=[],
            zscore_result={"is_anomaly": True, "z_score": 3.2},
            ml_result={"is_anomaly": True, "anomaly_score": -0.2, "ml_used": True},
        )
        self.assertEqual(decision["severity"], "HIGH")
        self.assertEqual(decision["source"], "combined")

    def test_zscore_only_results_in_medium(self):
        decision = DecisionEngine.combine(
            rule_signals=[],
            zscore_result={"is_anomaly": True, "z_score": 2.9},
            ml_result={"is_anomaly": False, "anomaly_score": 0.4, "ml_used": True},
        )
        self.assertEqual(decision["severity"], "MEDIUM")
        self.assertEqual(decision["source"], "zscore")

    def test_no_detection_results_in_normal(self):
        decision = DecisionEngine.combine(
            rule_signals=[],
            zscore_result={"is_anomaly": False, "z_score": 0.0},
            ml_result={"is_anomaly": False, "ml_used": True},
        )
        self.assertEqual(decision["severity"], "NORMAL")
        self.assertEqual(decision["source"], "none")


class PipelineOptimizationTests(unittest.TestCase):
    def test_rule_only_stays_high_when_other_detectors_do_not_trigger(self):
        pipeline = DetectionPipeline()

        class StubRuleEngine:
            def evaluate(self, event):
                return [{"signal_type": "HTTP_ERROR_SPIKE", "rule_id": "http_error_spike"}]

        class StubMLClient:
            def predict(self, features):
                return {
                    "is_anomaly": False,
                    "anomaly_score": 0.0,
                    "ml_used": True,
                    "error": None,
                    "source": "external",
                }

        class StubZScore:
            def evaluate(self, features):
                return {
                    "is_anomaly": False,
                    "z_score": 0.0,
                    "z_score_request_rate": 0.0,
                    "z_score_error_ratio": 0.0,
                }

        class StubStore:
            def save_detection_result(self, result):
                return None

        pipeline.rule_engine = StubRuleEngine()
        pipeline.ml_client = StubMLClient()
        pipeline.zscore_detector = StubZScore()
        pipeline.store = StubStore()

        event = {
            "event_id": "evt-rule-only",
            "event_type": "http.request",
            "service_name": "api-gateway",
            "environment": "prod",
            "region": "us-east-1",
            "risk_score": 0.8,
            "metadata": {"status": 500, "path": "/v1/payments"},
        }

        signals = pipeline.process(event)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["severity"], "HIGH")
        self.assertEqual(signals[0]["source"], "rule")

    def test_runtime_ml_path_is_used(self):
        pipeline = DetectionPipeline()

        class StubRuleEngine:
            def evaluate(self, event):
                return []

        class StubRuntimeML:
            def predict(self, features):
                return {
                    "is_anomaly": True,
                    "anomaly_score": 0.88,
                    "ml_used": True,
                    "error": None,
                    "source": "runtime",
                }

            def runtime_snapshot(self):
                return {"trained_samples": 1}

        class StubStore:
            def save_detection_result(self, result):
                return None

        class StubZScore:
            def evaluate(self, features):
                return {
                    "is_anomaly": False,
                    "z_score": 0.4,
                    "z_score_request_rate": 0.4,
                    "z_score_error_ratio": 0.2,
                }

        pipeline.rule_engine = StubRuleEngine()
        pipeline.ml_client = StubRuntimeML()
        pipeline.zscore_detector = StubZScore()
        pipeline.store = StubStore()

        event = {
            "event_id": "evt-ml-only",
            "timestamp": "2026-04-11T10:30:00Z",
            "event_type": "http.request",
            "service_name": "api-gateway",
            "environment": "prod",
            "region": "us-east-1",
            "risk_score": 0.4,
            "metadata": {"status": 500, "path": "/api/v1/payments"},
        }

        signals = pipeline.process(event)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["severity"], "MEDIUM")
        self.assertEqual(signals[0]["source"], "ml")
        self.assertEqual(signals[0]["metadata"]["ml_source"], "runtime")


if __name__ == "__main__":
    unittest.main()
