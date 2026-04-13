import unittest

from runtime_ml_model import RuntimeAnomalyModel


class RuntimeMLModelTests(unittest.TestCase):
    def test_model_trains_with_stream(self):
        model = RuntimeAnomalyModel()

        base = {
            "failed_login_count": 0,
            "request_rate": 1.0,
            "error_ratio": 0.01,
            "unique_ip_count": 1,
            "endpoint_entropy": 1.2,
            "time_of_day": 10,
        }

        for _ in range(30):
            out = model.predict(base)

        self.assertTrue(out["ml_used"])
        self.assertIsNotNone(out["anomaly_score"])
        self.assertGreaterEqual(out["trained_samples"], 30)

    def test_model_flags_large_outlier_after_warmup(self):
        model = RuntimeAnomalyModel()

        base = {
            "failed_login_count": 0,
            "request_rate": 1.0,
            "error_ratio": 0.01,
            "unique_ip_count": 1,
            "endpoint_entropy": 1.2,
            "time_of_day": 10,
        }

        for _ in range(35):
            model.predict(base)

        outlier = {
            "failed_login_count": 40,
            "request_rate": 80.0,
            "error_ratio": 0.95,
            "unique_ip_count": 45,
            "endpoint_entropy": 4.5,
            "time_of_day": 3,
        }

        predicted = model.predict(outlier)
        self.assertTrue(predicted["is_anomaly"])
        self.assertGreater(predicted["anomaly_score"], 0.5)


if __name__ == "__main__":
    unittest.main()
