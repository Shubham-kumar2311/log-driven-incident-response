from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch


# Keep execution offline and deterministic for assignment evidence.
os.environ.setdefault("ML_MODE", "runtime")

ROOT_DIR = Path(__file__).resolve().parents[2]
DETECTION_DIR = ROOT_DIR / "src" / "detection_service"

if str(DETECTION_DIR) not in sys.path:
    sys.path.insert(0, str(DETECTION_DIR))

from decision_engine import DecisionEngine
from ml_client import MLClient
from pipeline import DetectionPipeline


def _build_base_event(event_id: str, service_name: str, event_type: str) -> dict:
    return {
        "event_id": event_id,
        "service_name": service_name,
        "event_type": event_type,
        "timestamp": "2026-04-27T10:00:00Z",
        "metadata": {},
    }


def _get_problem(signal: dict) -> str:
    metadata = signal.get("metadata") or {}
    return metadata.get("rule_type") or "unknown"


def run_event_problem_cases() -> list[dict]:
    results: list[dict] = []

    # TC-DET-001
    pipeline = DetectionPipeline()
    event = _build_base_event("det-001", "api-gateway", "http.request")
    event["metadata"] = {"status": 200, "latency_ms": 120, "path": "/health"}
    signals = pipeline.process(event)
    results.append(
        {
            "id": "TC-DET-001",
            "expected_problem": "none",
            "actual_problem": "none" if not signals else _get_problem(signals[0]),
            "status": "PASS" if len(signals) == 0 else "FAIL",
            "signal_count": len(signals),
        }
    )

    # TC-DET-002
    pipeline = DetectionPipeline()
    event = _build_base_event("det-002", "api-gateway", "http.request")
    event["metadata"] = {"status": 200, "latency_ms": 3200, "path": "/checkout"}
    signals = pipeline.process(event)
    problem = _get_problem(signals[0]) if signals else "none"
    pass_case = len(signals) > 0 and "HIGH_LATENCY" in problem
    results.append(
        {
            "id": "TC-DET-002",
            "expected_problem": "HIGH_LATENCY",
            "actual_problem": problem,
            "status": "PASS" if pass_case else "FAIL",
            "signal_count": len(signals),
        }
    )

    # TC-DET-003
    pipeline = DetectionPipeline()
    last_signals: list[dict] = []
    for i in range(5):
        event = _build_base_event(f"det-003-{i+1}", "auth-service", "auth.login_failed")
        event["metadata"] = {"client_ip": "203.0.113.10"}
        last_signals = pipeline.process(event)
    problem = _get_problem(last_signals[0]) if last_signals else "none"
    pass_case = len(last_signals) > 0 and "BRUTE_FORCE_LOGIN" in problem
    results.append(
        {
            "id": "TC-DET-003",
            "expected_problem": "BRUTE_FORCE_LOGIN",
            "actual_problem": problem,
            "status": "PASS" if pass_case else "FAIL",
            "signal_count": len(last_signals),
        }
    )

    # TC-DET-004
    pipeline = DetectionPipeline()
    event = _build_base_event("det-004", "db-monitor", "db.query")
    event["metadata"] = {"latency_ms": 6500, "query": "SELECT * FROM orders"}
    signals = pipeline.process(event)
    problem = _get_problem(signals[0]) if signals else "none"
    pass_case = len(signals) > 0 and "DB_SLOW_QUERY" in problem
    results.append(
        {
            "id": "TC-DET-004",
            "expected_problem": "DB_SLOW_QUERY",
            "actual_problem": problem,
            "status": "PASS" if pass_case else "FAIL",
            "signal_count": len(signals),
        }
    )

    # TC-DET-005
    pipeline = DetectionPipeline()
    event = _build_base_event("det-005", "deployment-service", "deployment.failed")
    event["metadata"] = {"version": "v2.1.7", "reason": "crash_loop"}
    signals = pipeline.process(event)
    problem = _get_problem(signals[0]) if signals else "none"
    pass_case = len(signals) > 0 and "DEPLOYMENT_FAILURE" in problem
    results.append(
        {
            "id": "TC-DET-005",
            "expected_problem": "DEPLOYMENT_FAILURE",
            "actual_problem": problem,
            "status": "PASS" if pass_case else "FAIL",
            "signal_count": len(signals),
        }
    )

    # TC-DET-006
    pipeline = DetectionPipeline()
    last_signals = []
    for i in range(10):
        event = _build_base_event(f"det-006-{i+1}", "api-gateway", "http.request")
        event["metadata"] = {"status": 503, "path": "/orders"}
        last_signals = pipeline.process(event)
    problem = _get_problem(last_signals[0]) if last_signals else "none"
    pass_case = len(last_signals) > 0 and "HTTP_ERROR_SPIKE" in problem
    results.append(
        {
            "id": "TC-DET-006",
            "expected_problem": "HTTP_ERROR_SPIKE",
            "actual_problem": problem,
            "status": "PASS" if pass_case else "FAIL",
            "signal_count": len(last_signals),
        }
    )

    # TC-DET-007
    pipeline = DetectionPipeline()
    last_signals = []
    for i in range(5):
        event = _build_base_event(f"det-007-{i+1}", "cache-layer", "cache.connection_error")
        event["severity"] = "ERROR"
        event["message"] = "Redis cache connection timeout"
        last_signals = pipeline.process(event)
    problem = _get_problem(last_signals[0]) if last_signals else "none"
    pass_case = len(last_signals) > 0 and "CACHE_CONNECTION_ERROR" in problem
    results.append(
        {
            "id": "TC-DET-007",
            "expected_problem": "CACHE_CONNECTION_ERROR",
            "actual_problem": problem,
            "status": "PASS" if pass_case else "FAIL",
            "signal_count": len(last_signals),
        }
    )

    # TC-DET-008
    pipeline = DetectionPipeline()
    event = {
        "event_id": "det-008",
        "service_name": "api-gateway",
        "timestamp": "2026-04-27T10:08:00Z",
        "metadata": {"status": 500, "latency_ms": 5000},
    }
    signals = pipeline.process(event)
    results.append(
        {
            "id": "TC-DET-008",
            "expected_problem": "none",
            "actual_problem": "none" if not signals else _get_problem(signals[0]),
            "status": "PASS" if len(signals) == 0 else "FAIL",
            "signal_count": len(signals),
        }
    )

    return results


def run_defect_checks() -> list[dict]:
    defects: list[dict] = []

    # BUG-DET-001
    result = DecisionEngine.combine([], {"is_anomaly": "false"}, {"is_anomaly": "false"})
    defects.append(
        {
            "id": "BUG-DET-001",
            "observed": {
                "zscore_triggered": result.get("zscore_triggered"),
                "ml_triggered": result.get("ml_triggered"),
                "severity": result.get("severity"),
            },
            "reproduced": bool(result.get("zscore_triggered") or result.get("ml_triggered")),
        }
    )

    # BUG-DET-002
    raised = False
    exc_type = None
    try:
        DecisionEngine.combine(None, {}, {})
    except Exception as exc:  # noqa: BLE001
        raised = True
        exc_type = type(exc).__name__

    defects.append(
        {
            "id": "BUG-DET-002",
            "observed": {"exception_type": exc_type},
            "reproduced": raised,
        }
    )

    # BUG-DET-003
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = []

    client = MLClient(url="http://ml-service/predict", timeout=0.1)
    client.mode = "external"

    raised = False
    exc_type = None
    with patch("requests.post", return_value=response):
        try:
            client.predict({"request_rate": 10.0})
        except Exception as exc:  # noqa: BLE001
            raised = True
            exc_type = type(exc).__name__

    defects.append(
        {
            "id": "BUG-DET-003",
            "observed": {"exception_type": exc_type},
            "reproduced": raised,
        }
    )

    return defects


def main() -> None:
    print("Q2(a) Detection Event-to-Problem Execution Evidence")

    case_results = run_event_problem_cases()
    passed = sum(1 for item in case_results if item["status"] == "PASS")

    for item in case_results:
        print(
            f"{item['id']}: expected={item['expected_problem']} | "
            f"actual={item['actual_problem']} | signals={item['signal_count']} | {item['status']}"
        )

    print("-" * 72)
    print(f"Event-to-problem cases: {passed}/{len(case_results)} PASS")

    print("\n")
    # print("Q2(b) Defect Reproduction Evidence")

    # defects = run_defect_checks()
    # for defect in defects:
    #     print(
    #         f"{defect['id']}: reproduced={defect['reproduced']} | observed={json.dumps(defect['observed'])}"
    #     )

    # print("-" * 72)
    # print(json.dumps({"cases": case_results, "defects": defects}, indent=2))


if __name__ == "__main__":
    main()
