import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run black-box API tests defined in api_blackbox_test_suite.json"
    )
    parser.add_argument(
        "--suite",
        default="api_blackbox_test_suite.json",
        help="Path to test suite JSON file",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Override base_url from suite JSON",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds",
    )
    return parser.parse_args()


def load_suite(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def resolve_path_value(data, path: str):
    if not path.startswith("$"):
        raise ValueError(f"Unsupported json path: {path}")

    if path == "$":
        return data

    expr = path[1:]
    if expr.startswith("."):
        expr = expr[1:]

    tokens = re.finditer(r"([A-Za-z0-9_-]+)|\[(\d+)\]", expr)

    current = data
    for token in tokens:
        key = token.group(1)
        index = token.group(2)

        if key is not None:
            if not isinstance(current, dict) or key not in current:
                raise KeyError(f"Path not found at key '{key}' for path {path}")
            current = current[key]
            continue

        if index is not None:
            idx = int(index)
            if not isinstance(current, list):
                raise TypeError(f"Expected list at index access for path {path}")
            if idx >= len(current):
                raise IndexError(f"Index {idx} out of range for path {path}")
            current = current[idx]

    return current


def matches_type(value, expected_type: str) -> bool:
    expected_type = expected_type.lower()

    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None

    return False


def evaluate_assertion(payload, assertion: dict) -> tuple[bool, str]:
    path = assertion.get("path")
    if not path:
        return False, "Assertion missing 'path'"

    try:
        actual = resolve_path_value(payload, path)
    except Exception as exc:
        return False, str(exc)

    if "equals" in assertion and actual != assertion["equals"]:
        return False, f"{path} expected equals {assertion['equals']} but got {actual}"

    if "contains" in assertion:
        expected = assertion["contains"]
        if isinstance(actual, str):
            if expected not in actual:
                return False, f"{path} expected to contain '{expected}' but got '{actual}'"
        elif isinstance(actual, list):
            if expected not in actual:
                return False, f"{path} expected list to contain '{expected}' but got {actual}"
        else:
            return False, f"{path} contains assertion requires string or list, got {type(actual).__name__}"

    if "min_items" in assertion:
        if not isinstance(actual, list):
            return False, f"{path} min_items assertion requires list, got {type(actual).__name__}"
        if len(actual) < int(assertion["min_items"]):
            return False, f"{path} expected at least {assertion['min_items']} items but got {len(actual)}"

    if "items" in assertion:
        if not isinstance(actual, list):
            return False, f"{path} items assertion requires list, got {type(actual).__name__}"
        if len(actual) != int(assertion["items"]):
            return False, f"{path} expected {assertion['items']} items but got {len(actual)}"

    if "type" in assertion:
        expected_type = assertion["type"]
        if not matches_type(actual, expected_type):
            return False, f"{path} expected type {expected_type} but got {type(actual).__name__}"

    return True, "ok"


def send_request(base_url: str, request_spec: dict, headers: dict, timeout: float):
    method = str(request_spec.get("method", "GET")).upper()
    path = request_spec.get("path", "")
    url = f"{base_url.rstrip('/')}{path}"

    kwargs = {"headers": headers, "timeout": timeout}
    if "body" in request_spec:
        kwargs["json"] = request_spec["body"]

    response = requests.request(method, url, **kwargs)

    try:
        payload = response.json()
    except ValueError:
        payload = None

    return response.status_code, payload, response.text


def validate_response(expected: dict, status_code: int, payload) -> list[str]:
    errors: list[str] = []

    if "status_code" in expected and status_code != int(expected["status_code"]):
        errors.append(f"Expected status {expected['status_code']}, got {status_code}")

    required_keys = expected.get("required_json_keys", [])
    if required_keys:
        if not isinstance(payload, dict):
            errors.append("Expected JSON object response for required_json_keys check")
        else:
            for key in required_keys:
                if key not in payload:
                    errors.append(f"Missing required key: {key}")

    for assertion in expected.get("json_assertions", []):
        if payload is None:
            errors.append("Cannot evaluate json_assertions: response is not valid JSON")
            break
        ok, message = evaluate_assertion(payload, assertion)
        if not ok:
            errors.append(message)

    return errors


def run_case(case_id: str, case_name: str, request_spec: dict, expected: dict, base_url: str, headers: dict, timeout: float):
    try:
        status_code, payload, raw = send_request(base_url, request_spec, headers, timeout)
    except Exception as exc:
        return False, [f"Request failed: {exc}"]

    errors = validate_response(expected or {}, status_code, payload)
    if errors:
        debug_payload = payload if payload is not None else raw
        errors.append(f"Response payload: {debug_payload}")
        return False, errors

    return True, []


def main() -> int:
    args = parse_args()

    suite_path = Path(args.suite).resolve()
    if not suite_path.exists():
        print(f"Suite file not found: {suite_path}")
        return 2

    suite = load_suite(suite_path)
    base_url = args.base_url or os.getenv("DETECTION_BASE_URL") or suite.get("base_url", "http://localhost:8003")
    headers = dict(suite.get("default_headers", {}))

    total = 0
    passed = 0

    print("Running single_request_tests")
    for case in suite.get("single_request_tests", []):
        total += 1
        case_id = case.get("id", "unknown-id")
        case_name = case.get("name", "unnamed")
        ok, errors = run_case(
            case_id=case_id,
            case_name=case_name,
            request_spec=case.get("request", {}),
            expected=case.get("expected", {}),
            base_url=base_url,
            headers=headers,
            timeout=args.timeout,
        )
        if ok:
            passed += 1
            print(f"PASS {case_id}: {case_name}")
        else:
            print(f"FAIL {case_id}: {case_name}")
            for err in errors:
                print(f"  - {err}")

    print("Running stateful_scenarios")
    for scenario in suite.get("stateful_scenarios", []):
        scenario_id = scenario.get("id", "unknown-scenario")
        scenario_name = scenario.get("name", "unnamed")
        print(f"Scenario {scenario_id}: {scenario_name}")

        for step in scenario.get("steps", []):
            total += 1
            step_id = step.get("step_id", "unknown-step")
            ok, errors = run_case(
                case_id=step_id,
                case_name=scenario_name,
                request_spec=step.get("request", {}),
                expected=step.get("expected", {}),
                base_url=base_url,
                headers=headers,
                timeout=args.timeout,
            )
            if ok:
                passed += 1
                print(f"PASS {step_id}")
            else:
                print(f"FAIL {step_id}")
                for err in errors:
                    print(f"  - {err}")

    failed = total - passed
    print("\nSummary")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
