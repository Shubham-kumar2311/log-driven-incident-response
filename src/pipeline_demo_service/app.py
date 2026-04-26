import asyncio
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from config import (
    ACTUATOR_SERVICE_URL,
    CORS_ORIGINS,
    DETECTION_SERVICE_URL,
    HOST,
    INCIDENT_SERVICE_URL,
    LOG_LEVEL,
    PIPELINE_DEMO_TIMEOUT_SECONDS,
    PORT,
    PROCESSING_SERVICE_URL,
    RESPONSE_SERVICE_URL,
)
from ui.dashboard import render_dashboard_html


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("pipeline_demo_service")

RESPONSE_FALLBACK_BASE_URLS = ("http://localhost:8005", "http://localhost:8015")


PREBUILT_DEMO_LOGS: List[Dict[str, Any]] = [
    {
        "id": "deploy-failed",
        "label": "Deployment Failure",
        "description": "Canary deployment fails and triggers rollback.",
        "payload": {
            "event_type": "deployment.failed",
            "service_name": "deployment-service",
            "message": "Canary deployment failed after health checks",
            "log_level": "ERROR",
            "environment": "production",
            "status_code": 500,
            "latency_ms": 1800,
            "metadata": {
                "build_id": "build-2026-04-01",
                "region": "us-east-1",
                "strategy": "canary",
            },
        },
    },
    {
        "id": "db-degraded",
        "label": "Database Degradation",
        "description": "Slow database query exceeding rule threshold.",
        "payload": {
            "event_type": "db.query",
            "service_name": "db-monitor",
            "message": "Checkout query exceeded latency threshold",
            "log_level": "ERROR",
            "environment": "production",
            "status_code": 500,
            "latency_ms": 4600,
            "metadata": {
                "cluster": "orders-primary",
                "latency_ms": 4600,
                "duration_ms": 4600,
                "query_signature": "orders_by_customer_with_items",
            },
        },
    },
    {
        "id": "deploy-failed-staging",
        "label": "Deployment Failure (Staging)",
        "description": "Deployment failure scenario in staging environment.",
        "payload": {
            "event_type": "deployment.failed",
            "service_name": "deployment-service",
            "message": "Staging deployment failed smoke tests",
            "log_level": "ERROR",
            "environment": "staging",
            "status_code": 500,
            "latency_ms": 2400,
            "metadata": {
                "build_id": "build-2026-04-03",
                "reason": "Integration smoke test failure",
                "version": "v2.8.2-rc1",
            },
        },
    },
]


class PipelineDemoRequest(BaseModel):
    event_type: str = Field(default="deployment.failed")
    service_name: str = Field(default="deployment-service")
    message: str = Field(default="Pipeline demo event")
    log_level: str = Field(default="ERROR")
    environment: str = Field(default="production")
    status_code: int = Field(default=500)
    latency_ms: int = Field(default=1200)
    metadata: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="Pipeline Demo Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _service_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _safe_json(text: str) -> Any:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _http_error_message(body: Any, raw_text: str, status_code: Optional[int]) -> str:
    if isinstance(body, dict):
        detail = body.get("detail") or body.get("error") or body.get("message")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    if raw_text.strip():
        return raw_text.strip()[:500]
    if status_code is not None:
        return f"HTTP {status_code}"
    return "Request failed"


def _sync_http_json(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]],
    timeout: float,
) -> Dict[str, Any]:
    headers = {"Accept": "application/json"}
    data: Optional[bytes] = None

    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())

    raw_text = ""
    status_code: Optional[int] = None

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            raw_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        raw_text = exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status_code": None,
            "body": {},
            "error": str(exc.reason) if getattr(exc, "reason", None) else str(exc),
        }

    body = _safe_json(raw_text)
    ok = bool(status_code is not None and 200 <= status_code < 300)

    return {
        "ok": ok,
        "status_code": status_code,
        "body": body if isinstance(body, dict) else {"payload": body},
        "error": None if ok else _http_error_message(body, raw_text, status_code),
    }


async def _http_json(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = PIPELINE_DEMO_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    return await asyncio.to_thread(_sync_http_json, method, url, payload, timeout)


async def _check_pipeline_service(name: str, base_url: str) -> Dict[str, Any]:
    health_url = _service_url(base_url, "/health")
    probe = await _http_json("GET", health_url, payload=None, timeout=PIPELINE_DEMO_TIMEOUT_SECONDS)
    return {
        "service": name,
        "url": health_url,
        "ok": probe["ok"],
        "status_code": probe["status_code"],
        "error": probe["error"],
        "response": probe["body"],
    }


async def _pipeline_health_snapshot() -> Dict[str, Any]:
    checks = await asyncio.gather(
        _check_pipeline_service("processing", PROCESSING_SERVICE_URL),
        _check_pipeline_service("detection", DETECTION_SERVICE_URL),
        _check_pipeline_service("incident_management", INCIDENT_SERVICE_URL),
        _check_response_service_health(),
        _check_pipeline_service("actuator", ACTUATOR_SERVICE_URL),
    )
    return {
        "ok": all(item.get("ok") for item in checks),
        "services": checks,
    }


def _response_base_url_candidates() -> List[str]:
    candidates = [RESPONSE_SERVICE_URL]
    for fallback_url in RESPONSE_FALLBACK_BASE_URLS:
        if fallback_url not in candidates:
            candidates.append(fallback_url)
    return candidates


async def _check_response_service_health() -> Dict[str, Any]:
    probes: List[Dict[str, Any]] = []
    for base_url in _response_base_url_candidates():
        probe = await _check_pipeline_service("response", base_url)
        probe_record = dict(probe)
        probes.append(probe_record)
        if probe_record.get("ok"):
            return {
                **probe_record,
                "probes": [dict(item) for item in probes],
            }

    if probes:
        return {
            **probes[0],
            "probes": [dict(item) for item in probes],
        }

    return {
        "service": "response",
        "url": _service_url(RESPONSE_SERVICE_URL, "/health"),
        "ok": False,
        "status_code": None,
        "error": "No response service probes available",
        "response": {},
        "probes": [],
    }


async def _latest_actuator_execution() -> Optional[Dict[str, Any]]:
    history_url = _service_url(ACTUATOR_SERVICE_URL, "/history?limit=1")
    history = await _http_json("GET", history_url, payload=None, timeout=PIPELINE_DEMO_TIMEOUT_SECONDS)
    if not history.get("ok"):
        return None

    body = history.get("body")
    if not isinstance(body, dict):
        return None

    executions = body.get("executions")
    if not isinstance(executions, list) or not executions:
        return None

    latest = executions[0]
    return latest if isinstance(latest, dict) else None


def _extract_actuator_received_payload(execution: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(execution, dict):
        return {}

    payload = execution.get("actuator_received_payload")
    if isinstance(payload, dict):
        return payload

    # Backward-compatible fallback while old records may still exist.
    detail = execution.get("detail")
    if isinstance(detail, dict):
        return detail

    return {}


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return render_dashboard_html()


@app.get("/api/info")
def api_info() -> Dict[str, Any]:
    return {
        "service": "pipeline-demo-service",
        "status": "running",
        "message": "Use /demo/pipeline-run with one prebuilt payload from /demo/prebuilt-logs",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "pipeline-demo-service",
        "prebuilt_logs": len(PREBUILT_DEMO_LOGS),
    }


@app.get("/demo/prebuilt-logs")
def prebuilt_logs() -> Dict[str, Any]:
    return {
        "count": len(PREBUILT_DEMO_LOGS),
        "items": PREBUILT_DEMO_LOGS,
    }


@app.get("/demo/pipeline-health")
async def pipeline_health() -> Dict[str, Any]:
    return await _pipeline_health_snapshot()


@app.post("/demo/pipeline-run")
async def pipeline_run(payload: PipelineDemoRequest) -> Dict[str, Any]:
    demo_id = f"demo-{int(datetime.utcnow().timestamp())}"
    health = await _pipeline_health_snapshot()
    steps: List[Dict[str, Any]] = []

    metadata = {
        "status": payload.status_code,
        "status_code": payload.status_code,
        "latency_ms": payload.latency_ms,
        "duration_ms": payload.latency_ms,
        "pipeline_demo_id": demo_id,
    }
    metadata.update(payload.metadata)

    raw_event = {
        "event_id": demo_id,
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": payload.event_type,
        "service_name": payload.service_name,
        "log_level": payload.log_level,
        "message": payload.message,
        "environment": payload.environment,
        "metadata": metadata,
    }

    processing_url = _service_url(PROCESSING_SERVICE_URL, "/process")
    processing = await _http_json(
        "POST",
        processing_url,
        payload=raw_event,
        timeout=PIPELINE_DEMO_TIMEOUT_SECONDS,
    )
    processing_summary = processing["body"].get("status") if isinstance(processing["body"], dict) else None
    processing_ok = processing["ok"] and processing_summary == "processed"
    steps.append(
        {
            "step": "processing",
            "ok": processing_ok,
            "status_code": processing["status_code"],
            "error": processing["error"],
            "summary": processing_summary,
        }
    )
    if not processing["ok"]:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Processing step failed",
                "failed_step": "processing",
                "steps": steps,
            },
        )
    if not processing_ok:
        return {
            "demo_id": demo_id,
            "status": "incomplete",
            "reason": "Processing pipeline dropped the event payload",
            "pipeline_health": health,
            "raw_event": raw_event,
            "processed_event": None,
            "actuator_execution": None,
            "actuator_received_payload": {},
            "signals": [],
            "steps": steps,
        }

    processed_event = processing["body"].get("processed_event")
    if not isinstance(processed_event, dict):
        processed_event = raw_event

    latest_actuator_execution = await _latest_actuator_execution()
    actuator_received_payload = _extract_actuator_received_payload(latest_actuator_execution)

    return {
        "demo_id": demo_id,
        "status": "accepted",
        "mode": "processing_trigger_only",
        "message": (
            "Event sent to processing. Downstream services should continue the flow "
            "through existing service-to-service forwarding."
        ),
        "pipeline_health": health,
        "raw_event": raw_event,
        "processed_event": processed_event,
        "actuator_execution": latest_actuator_execution,
        "actuator_received_payload": actuator_received_payload,
        "latest_actuator_execution": latest_actuator_execution,
        "steps": steps,
        "next_hops": [
            {
                "from": "processing",
                "to": "detection",
                "target": _service_url(DETECTION_SERVICE_URL, "/detect"),
            },
            {
                "from": "detection",
                "to": "incident_management",
                "target": _service_url(INCIDENT_SERVICE_URL, "/signals"),
            },
            {
                "from": "incident_management",
                "to": "response",
                "target": _service_url(RESPONSE_SERVICE_URL, "/simulate-response"),
            },
            {
                "from": "response",
                "to": "actuator",
                "target": _service_url(ACTUATOR_SERVICE_URL, "/execute"),
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
