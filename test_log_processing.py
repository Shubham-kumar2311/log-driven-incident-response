from pathlib import Path
import sys

import pytest


LOG_PROCESSING_DIR = Path(__file__).resolve().parent / "src" / "log_processing_service"
if str(LOG_PROCESSING_DIR) not in sys.path:
    sys.path.insert(0, str(LOG_PROCESSING_DIR))

from pipeline import ProcessingPipeline
from processors.feature_extractor import FeatureExtractor
from processors.normalizer import Normalizer
from processors.validator import Validator


@pytest.fixture()
def pipeline():
    return ProcessingPipeline()


@pytest.mark.parametrize(
    "raw_event,expected_normalized,expected_severity",
    [
        pytest.param(
            {
                "event_id": "evt-1",
                "timestamp": "2026-01-01T00:00:00Z",
                "service_name": "api-gateway",
                "log_level": "INFO",
                "event_type": "http.request",
                "message": "request complete",
                "metadata": {"status_code": 200, "latency_ms": 150},
            },
            "HTTP_SUCCESS",
            "LOW",
            id="http-2xx",
        ),
        pytest.param(
            {
                "event_id": "evt-2",
                "timestamp": "2026-01-01T00:00:00Z",
                "service": "api-gateway",
                "level": "ERROR",
                "event": "http.request",
                "message": "server error",
                "metadata": {"status": 503, "latency_ms": 1200},
            },
            "HTTP_SERVER_ERROR",
            "HIGH",
            id="alias-fields-http-5xx",
        ),
        pytest.param(
            {
                "event_id": "evt-3",
                "timestamp": "2026-01-01T00:00:00Z",
                "service_name": "db-monitor",
                "log_level": "WARN",
                "event_type": "db.query",
                "message": "slow query",
                "metadata": {"duration_ms": 7000, "query_type": "SELECT", "table": "users"},
            },
            "DB_SLOW_QUERY",
            "HIGH",
            id="db-query-slow",
        ),
    ],
)
def test_pipeline_black_box_valid_logs(pipeline, raw_event, expected_normalized, expected_severity):
    out = pipeline.process(raw_event)

    assert out is not None
    assert out["normalized_type"] == expected_normalized
    assert out["severity"] == expected_severity
    assert isinstance(out["timestamp"], str)
    assert isinstance(out["processed_at"], str)
    assert isinstance(out["features"], dict)
    assert out["message"] == raw_event["message"]


@pytest.mark.parametrize(
    "bad_event",
    [
        pytest.param({}, id="empty-log"),
        pytest.param({"service_name": "api", "log_level": "INFO"}, id="missing-event-type"),
        pytest.param({"event_type": "http.request", "log_level": "INFO"}, id="missing-service"),
        pytest.param("totally corrupted line", id="corrupted-line-string"),
        pytest.param(None, id="null-value"),
        pytest.param({"service_name": "api", "log_level": "INFO", "event_type": "http.request", "metadata": "not-a-dict"}, id="malformed-metadata"),
    ],
)
def test_pipeline_malformed_or_missing_inputs_do_not_crash(pipeline, bad_event):
    out = pipeline.process(bad_event)
    assert out is None


def test_pipeline_missing_level_uses_default_info(pipeline):
    out = pipeline.process(
        {
            "service_name": "api",
            "event_type": "http.request",
            "message": "no level provided",
            "metadata": {"status_code": 200},
        }
    )

    assert out is not None
    assert out["log_level"] == "INFO"


def test_pipeline_unexpected_format_and_incorrect_timestamp_still_processes(pipeline):
    event = {
        "event_id": "evt-unexpected",
        "timestamp": "not-a-timestamp",
        "service_name": "api-gateway",
        "log_level": "INFO",
        "event_type": "http.request",
        "message": None,
        "metadata": {"status_code": "abc", "latency_ms": "bad-number"},
    }

    out = pipeline.process(event)

    assert out is not None
    assert out["timestamp"] == "not-a-timestamp"
    assert out["normalized_type"] == "HTTP_SUCCESS"
    assert out["message"] is None
    assert "status_code" not in out["features"]
    assert "latency_ms" not in out["features"]


@pytest.mark.parametrize(
    "status,expected_norm,expected_severity",
    [
        pytest.param(503, "HTTP_SERVER_ERROR", "HIGH", id="status-5xx"),
        pytest.param(404, "HTTP_CLIENT_ERROR", "MEDIUM", id="status-4xx"),
        pytest.param(301, "HTTP_REDIRECT", "INFO", id="status-3xx"),
        pytest.param(200, "HTTP_SUCCESS", "LOW", id="status-2xx"),
        pytest.param("invalid", "HTTP_SUCCESS", "LOW", id="status-invalid-default"),
    ],
)
def test_normalizer_http_branch_coverage(status, expected_norm, expected_severity):
    normalizer = Normalizer()
    event = {
        "event_type": "http.request",
        "log_level": "INFO",
        "metadata": {"status_code": status},
    }

    out = normalizer.process(event)

    assert out["normalized_type"] == expected_norm
    assert out["severity"] == expected_severity


@pytest.mark.parametrize(
    "duration,expected_norm,expected_severity",
    [
        pytest.param(6000, "DB_SLOW_QUERY", "HIGH", id="db-very-slow"),
        pytest.param(3000, "DB_SLOW_QUERY", "MEDIUM", id="db-moderately-slow"),
        pytest.param(200, "DB_QUERY", "LOW", id="db-normal"),
        pytest.param("bad", "DB_QUERY", "LOW", id="db-invalid-duration"),
    ],
)
def test_normalizer_db_query_branch_coverage(duration, expected_norm, expected_severity):
    normalizer = Normalizer()
    event = {
        "event_type": "db.query",
        "log_level": "INFO",
        "metadata": {"duration_ms": duration},
    }

    out = normalizer.process(event)

    assert out["normalized_type"] == expected_norm
    assert out["severity"] == expected_severity


def test_normalizer_error_level_override_branch():
    normalizer = Normalizer()
    out = normalizer.process(
        {
            "event_type": "deploy.completed",
            "log_level": "ERROR",
            "metadata": {},
        }
    )

    assert out["normalized_type"] == "DEPLOY_COMPLETED"
    assert out["severity"] == "HIGH"


def test_validator_resolves_dual_fields_and_generates_defaults():
    validator = Validator()
    out = validator.process(
        {
            "service": "api-gateway",
            "level": "warn",
            "event": "http.request",
            "message": "ok",
            "metadata": {},
        }
    )

    assert out is not None
    assert out["service_name"] == "api-gateway"
    assert out["log_level"] == "WARN"
    assert out["event_type"] == "http.request"
    assert isinstance(out["event_id"], str)
    assert isinstance(out["timestamp"], str)
    assert out["timestamp"].endswith("Z")


def test_feature_extractor_branch_coverage():
    extractor = FeatureExtractor()
    event = {
        "service_name": "worker-service",
        "severity": "HIGH",
        "normalized_type": "WORKER_JOB_FAILED",
        "metadata": {
            "latency_ms": 1200,
            "duration_ms": 8000,
            "status_code": 500,
            "job": "daily-sync",
            "retries": 3,
            "reason": "timeout",
        },
    }

    out = extractor.process(event)

    assert out is not None
    features = out["features"]
    assert features["latency_bucket"] == "HIGH"
    assert features["duration_bucket"] == "HIGH"
    assert features["is_error_response"] is True
    assert features["job_name"] == "daily-sync"
    assert features["retry_count"] == 3
    assert features["failure_reason"] == "timeout"


def test_pipeline_large_input_batch(pipeline):
    valid = {
        "timestamp": "2026-01-01T00:00:00Z",
        "service_name": "api-gateway",
        "log_level": "INFO",
        "event_type": "http.request",
        "message": "batch",
        "metadata": {"status_code": 200, "latency_ms": 100},
    }

    invalid = {
        "service_name": "api-gateway",
        "log_level": "INFO",
        "message": "missing event_type",
    }

    events = [dict(valid, event_id=f"ok-{i}") for i in range(450)]
    events.extend([dict(invalid, event_id=f"bad-{i}") for i in range(50)])

    results = pipeline.process_batch(events)

    assert len(results) == 450
    assert all(r["normalized_type"] == "HTTP_SUCCESS" for r in results)
    assert all(isinstance(r["features"], dict) for r in results)
