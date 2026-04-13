from pathlib import Path
import importlib.util
import sys
from unittest.mock import Mock

import pytest
import requests
from pydantic import ValidationError


ROOT_DIR = Path(__file__).resolve().parent
ML_SERVICE_DIR = ROOT_DIR / "src" / "ml_service"
DETECTION_SERVICE_DIR = ROOT_DIR / "src" / "detection_service"

for path in (ML_SERVICE_DIR, DETECTION_SERVICE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import app as ml_app


def _load_detection_ml_client_class():
    config_path = DETECTION_SERVICE_DIR / "config.py"
    ml_client_path = DETECTION_SERVICE_DIR / "ml_client.py"

    old_config = sys.modules.get("config")

    config_spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(config_spec)
    assert config_spec is not None and config_spec.loader is not None
    sys.modules["config"] = config_module
    config_spec.loader.exec_module(config_module)

    client_spec = importlib.util.spec_from_file_location("detection_ml_client", ml_client_path)
    client_module = importlib.util.module_from_spec(client_spec)
    assert client_spec is not None and client_spec.loader is not None
    client_spec.loader.exec_module(client_module)

    if old_config is not None:
        sys.modules["config"] = old_config
    else:
        sys.modules.pop("config", None)

    return client_module.MLClient


MLClient = _load_detection_ml_client_class()


@pytest.fixture(autouse=True)
def restore_global_model():
    old = ml_app.model
    yield
    ml_app.model = old


@pytest.fixture()
def payload():
    return ml_app.PredictPayload(
        request_rate=12.5,
        error_ratio=0.05,
        failed_login_count=1,
        unique_ip_count=3,
        endpoint_entropy=2.7,
        time_of_day=11,
        z_score_request_rate=0.9,
        z_score_error_ratio=0.4,
    )


@pytest.fixture()
def mock_model():
    return Mock()


@pytest.mark.parametrize(
    "score,expected_anomaly",
    [
        pytest.param(-0.5, True, id="anomaly-detected"),
        pytest.param(0.2, False, id="normal-case"),
        pytest.param(0.0, False, id="threshold-boundary"),
    ],
)
def test_predict_with_mocked_model_scores(payload, mock_model, score, expected_anomaly):
    mock_model.decision_function.return_value = [score]
    ml_app.model = mock_model

    out = ml_app.predict(payload)

    assert set(out.keys()) == {"is_anomaly", "anomaly_score"}
    assert out["is_anomaly"] is expected_anomaly
    assert out["anomaly_score"] == float(score)
    assert isinstance(out["is_anomaly"], bool)
    assert isinstance(out["anomaly_score"], float)


@pytest.mark.parametrize(
    "field,value",
    [
        pytest.param("request_rate", "not-a-number", id="invalid-request-rate"),
        pytest.param("error_ratio", None, id="null-error-ratio"),
        pytest.param("time_of_day", "midnight", id="invalid-time-of-day"),
    ],
)
def test_predict_payload_validation_errors(field, value):
    payload_dict = {
        "request_rate": 1.0,
        "error_ratio": 0.1,
        "failed_login_count": 0,
        "unique_ip_count": 1,
        "endpoint_entropy": 2.0,
        "time_of_day": 0,
        "z_score_request_rate": 0.0,
        "z_score_error_ratio": 0.0,
    }
    payload_dict[field] = value

    with pytest.raises(ValidationError):
        ml_app.PredictPayload(**payload_dict)


def test_predict_raises_when_model_not_loaded(payload):
    ml_app.model = None

    with pytest.raises(Exception) as exc_info:
        ml_app.predict(payload)

    assert "Model not loaded" in str(exc_info.value)


def test_predict_model_failure_propagates_exception(payload, mock_model):
    mock_model.decision_function.side_effect = RuntimeError("model boom")
    ml_app.model = mock_model

    with pytest.raises(RuntimeError, match="model boom"):
        ml_app.predict(payload)


def test_mlclient_external_success_uses_mocked_response(monkeypatch):
    client = MLClient(url="http://ml-service/predict", timeout=0.1)
    client.mode = "external"

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"is_anomaly": True, "anomaly_score": -0.11}

    def fake_post(url, json, timeout):
        return response

    monkeypatch.setattr(requests, "post", fake_post)

    out = client.predict({"request_rate": 99.0})

    assert out["is_anomaly"] is True
    assert out["anomaly_score"] == -0.11
    assert out["ml_used"] is True
    assert out["error"] is None
    assert out["source"] == "external"


def test_mlclient_external_timeout_graceful_fallback(monkeypatch):
    client = MLClient(url="http://ml-service/predict", timeout=0.01)
    client.mode = "external"

    def fake_post(url, json, timeout):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(requests, "post", fake_post)

    out = client.predict({"request_rate": 99.0})

    assert out["is_anomaly"] is False
    assert out["anomaly_score"] is None
    assert out["ml_used"] is True
    assert out["error"] == "timeout"
    assert out["source"] == "external"
    assert set(out.keys()) == {"is_anomaly", "anomaly_score", "ml_used", "error", "source"}


def test_mlclient_hybrid_falls_back_to_runtime_on_request_failure(monkeypatch):
    client = MLClient(url="http://ml-service/predict", timeout=0.01)
    client.mode = "hybrid"

    def fake_post(url, json, timeout):
        raise requests.RequestException("unavailable")

    monkeypatch.setattr(requests, "post", fake_post)

    out = client.predict(
        {
            "failed_login_count": 0,
            "request_rate": 1.0,
            "error_ratio": 0.01,
            "unique_ip_count": 1,
            "endpoint_entropy": 1.1,
            "time_of_day": 10,
        }
    )

    assert out["ml_used"] is True
    assert out["source"] == "runtime_fallback"
    assert "fallback_runtime" in (out["error"] or "")
    assert isinstance(out["is_anomaly"], bool)
    assert isinstance(out["anomaly_score"], float)