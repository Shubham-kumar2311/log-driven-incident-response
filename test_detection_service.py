from pathlib import Path
import sys

import pytest


DETECTION_SERVICE_DIR = Path(__file__).resolve().parent / "src" / "detection_service"
if str(DETECTION_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(DETECTION_SERVICE_DIR))

from decision_engine import DecisionEngine


@pytest.mark.parametrize(
    "rule_signals,zscore_result,ml_result,expected",
    [
        pytest.param([], {"is_anomaly": False}, {"is_anomaly": False}, {"severity": "NORMAL", "source": "none", "detection_source": "none", "rule": False, "z": False, "ml": False}, id="no-signals-normal"),
        pytest.param([{"signal_type": "HTTP_ERROR_SPIKE", "rule_id": "r1"}], {"is_anomaly": False}, {"is_anomaly": False, "ml_used": True}, {"severity": "HIGH", "source": "rule", "detection_source": "rule", "rule": True, "z": False, "ml": False}, id="rule-only-high"),
        pytest.param([], {"is_anomaly": True, "z_score": 3.1}, {"is_anomaly": False}, {"severity": "MEDIUM", "source": "zscore", "detection_source": "zscore", "rule": False, "z": True, "ml": False}, id="zscore-only-medium"),
        pytest.param([], {"is_anomaly": False}, {"is_anomaly": True, "anomaly_score": 0.82, "ml_used": True}, {"severity": "MEDIUM", "source": "ml", "detection_source": "ml", "rule": False, "z": False, "ml": True}, id="ml-only-medium"),
        pytest.param([{"signal_type": "AUTH_FAILURE", "rule_id": "r-auth"}], {"is_anomaly": False}, {"is_anomaly": True, "anomaly_score": 0.91, "ml_used": True}, {"severity": "CRITICAL", "source": "combined", "detection_source": "rule+ml", "rule": True, "z": False, "ml": True}, id="rule-plus-ml-critical"),
        pytest.param([], {"is_anomaly": True, "z_score": 2.5}, {"is_anomaly": True, "anomaly_score": -0.2, "ml_used": True}, {"severity": "HIGH", "source": "combined", "detection_source": "zscore+ml", "rule": False, "z": True, "ml": True}, id="zscore-plus-ml-high"),
        pytest.param([{"signal_type": "LATENCY_SPIKE", "rule_id": "r-lat"}], {"is_anomaly": True, "z_score": 2.8}, {"is_anomaly": True, "anomaly_score": -0.6, "ml_used": True}, {"severity": "CRITICAL", "source": "combined", "detection_source": "rule+zscore+ml", "rule": True, "z": True, "ml": True}, id="all-three-critical"),
    ],
)
def test_decision_engine_combine_matrix(rule_signals, zscore_result, ml_result, expected):
    result = DecisionEngine.combine(rule_signals, zscore_result, ml_result)

    assert result["severity"] == expected["severity"]
    assert result["source"] == expected["source"]
    assert result["detection_source"] == expected["detection_source"]
    assert result["rule_triggered"] is expected["rule"]
    assert result["zscore_triggered"] is expected["z"]
    assert result["ml_triggered"] is expected["ml"]


@pytest.mark.parametrize(
    "rule_signals,zscore_result,ml_result",
    [
        pytest.param([], None, None, id="none-optionals"),
        pytest.param([], {}, {}, id="empty-dicts"),
        pytest.param([], {"is_anomaly": False}, None, id="ml-none"),
    ],
)
def test_decision_engine_empty_inputs_are_handled(rule_signals, zscore_result, ml_result):
    result = DecisionEngine.combine(rule_signals, zscore_result, ml_result)

    assert result["severity"] == "NORMAL"
    assert result["source"] == "none"
    assert result["detection_source"] == "none"
    assert result["rule_triggered"] is False
    assert result["zscore_triggered"] is False
    assert result["ml_triggered"] is False


@pytest.mark.parametrize(
    "rule_signals,zscore_result,ml_result",
    [
        pytest.param(None, {}, {}, id="rule-signals-none"),
        pytest.param("not-a-list", {}, {}, id="rule-signals-string"),
        pytest.param(42, {}, {}, id="rule-signals-int"),
    ],
)
def test_decision_engine_malformed_rule_signals_raise(rule_signals, zscore_result, ml_result):
    with pytest.raises((TypeError, AttributeError)):
        DecisionEngine.combine(rule_signals, zscore_result, ml_result)


def test_decision_engine_malformed_boolean_inputs_cast_to_bool():
    result = DecisionEngine.combine(
        [{"rule_id": "r1"}],
        {"is_anomaly": "yes", "z_score": "2.0"},
        {"is_anomaly": 1, "anomaly_score": "0.95", "ml_used": "true", "error": "none"},
    )

    assert result["severity"] == "CRITICAL"
    assert result["source"] == "combined"
    assert result["zscore_triggered"] is True
    assert result["ml_triggered"] is True
    assert result["ml_used"] is True


def test_decision_engine_multiple_rule_signals_and_deduplication():
    rule_signals = [
        {"signal_type": "AUTH_FAILURE", "rule_id": "r-auth"},
        {"signal_type": "LATENCY_SPIKE", "rule_id": "r-lat"},
        {"signal_type": "AUTH_FAILURE", "rule_id": "r-auth"},
        {"rule_id": "db_slow_query"},
    ]

    result = DecisionEngine.combine(rule_signals, {"is_anomaly": False}, {"is_anomaly": False})

    assert result["severity"] == "HIGH"
    assert result["rule_triggered"] is True
    assert result["rule_type"] == "AUTH_FAILURE,LATENCY_SPIKE,db_slow_query"
    assert result["rule_type"].count("AUTH_FAILURE") == 1


def test_decision_engine_output_contains_expected_fields():
    result = DecisionEngine.combine(
        [{"signal_type": "HTTP_ERROR_SPIKE", "rule_id": "r-http"}],
        {"is_anomaly": True, "z_score": 2.4, "z_score_request_rate": 1.8, "z_score_error_ratio": 2.4},
        {"is_anomaly": True, "anomaly_score": -0.4, "ml_used": True, "error": None},
    )

    expected_keys = {
        "rule_triggered",
        "zscore_triggered",
        "ml_triggered",
        "severity",
        "source",
        "detection_source",
        "anomaly_score",
        "z_score",
        "z_score_request_rate",
        "z_score_error_ratio",
        "rule_type",
        "ml_used",
        "ml_error",
    }

    assert expected_keys.issubset(result.keys())
    assert isinstance(result["severity"], str)
    assert isinstance(result["source"], str)
    assert isinstance(result["detection_source"], str)
    assert isinstance(result["rule_triggered"], bool)
    assert isinstance(result["zscore_triggered"], bool)
    assert isinstance(result["ml_triggered"], bool)
