import logging
import time

import requests

from config import ML_MAX_RETRIES, ML_MODE, ML_REQUEST_TIMEOUT_SECONDS, ML_SERVICE_URL
from runtime_ml_model import RuntimeAnomalyModel

logger = logging.getLogger("detection.ml_client")


class MLClient:
    """ML inference client supporting runtime, external, or hybrid mode."""

    def __init__(self, url: str = ML_SERVICE_URL, timeout: float = ML_REQUEST_TIMEOUT_SECONDS):
        self.url = url
        self.timeout = timeout
        self.mode = ML_MODE
        self.max_retries = max(0, ML_MAX_RETRIES)
        self.runtime_model = RuntimeAnomalyModel()

    def _predict_external(self, features: dict) -> dict:
        if not self.url:
            return {
                "is_anomaly": False,
                "anomaly_score": None,
                "ml_used": False,
                "error": "ML_SERVICE_URL not configured",
                "source": "external",
            }

        attempts = self.max_retries + 1
        last_error: Exception | None = None
        payload = None

        for attempt in range(1, attempts + 1):
            try:
                response = requests.post(self.url, json=features, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                break
            except (requests.Timeout, requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt >= attempts:
                    raise
                sleep_seconds = 0.1 * attempt
                logger.warning(
                    "ML request failed; retrying",
                    extra={"attempt": attempt, "max_attempts": attempts, "sleep_seconds": sleep_seconds},
                )
                time.sleep(sleep_seconds)

        if payload is None:
            if last_error:
                raise last_error
            raise RuntimeError("ML response payload missing")

        return {
            "is_anomaly": bool(payload.get("is_anomaly", False)),
            "anomaly_score": payload.get("anomaly_score"),
            "ml_used": True,
            "error": None,
            "source": "external",
        }

    def _predict_runtime(self, features: dict) -> dict:
        return self.runtime_model.predict(features)

    def predict(self, features: dict) -> dict:
        if self.mode == "runtime":
            return self._predict_runtime(features)

        if self.mode == "external":
            try:
                return self._predict_external(features)
            except requests.Timeout:
                logger.warning("ML service timeout", extra={"ml_url": self.url})
                return {
                    "is_anomaly": False,
                    "anomaly_score": None,
                    "ml_used": True,
                    "error": "timeout",
                    "source": "external",
                }
            except requests.RequestException:
                logger.exception("ML service request failed")
                return {
                    "is_anomaly": False,
                    "anomaly_score": None,
                    "ml_used": True,
                    "error": "request_failed",
                    "source": "external",
                }
            except ValueError:
                logger.exception("ML service returned invalid JSON")
                return {
                    "is_anomaly": False,
                    "anomaly_score": None,
                    "ml_used": True,
                    "error": "invalid_json",
                    "source": "external",
                }

        # hybrid mode: try external first, fallback to runtime model
        try:
            return self._predict_external(features)
        except requests.Timeout:
            logger.warning("External ML timeout in hybrid mode, falling back to runtime model")
            fallback = self._predict_runtime(features)
            fallback["error"] = "external_timeout_fallback_runtime"
            fallback["source"] = "runtime_fallback"
            return fallback
        except requests.RequestException:
            logger.exception("External ML request failed in hybrid mode, falling back to runtime model")
            fallback = self._predict_runtime(features)
            fallback["error"] = "external_request_failed_fallback_runtime"
            fallback["source"] = "runtime_fallback"
            return fallback
        except ValueError:
            logger.exception("External ML invalid response in hybrid mode, falling back to runtime model")
            fallback = self._predict_runtime(features)
            fallback["error"] = "external_invalid_json_fallback_runtime"
            fallback["source"] = "runtime_fallback"
            return fallback

    def runtime_snapshot(self) -> dict:
        return self.runtime_model.snapshot()
