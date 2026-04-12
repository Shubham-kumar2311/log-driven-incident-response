import unittest

from zscore_detector import ZScoreDetector


class ZScoreDetectorTests(unittest.TestCase):
    def test_emits_anomaly_after_history_warmup(self):
        detector = ZScoreDetector(threshold=2.0, min_samples=5)

        baseline = {
            "request_rate": 10.0,
            "error_ratio": 0.1,
        }
        for _ in range(8):
            out = detector.evaluate(baseline)
            self.assertFalse(out["is_anomaly"])

        spike = detector.evaluate({"request_rate": 100.0, "error_ratio": 0.95})
        self.assertTrue(spike["is_anomaly"])
        self.assertGreater(spike["z_score"], 2.0)
        self.assertIn("z_score_request_rate", spike)
        self.assertIn("z_score_error_ratio", spike)


if __name__ == "__main__":
    unittest.main()
