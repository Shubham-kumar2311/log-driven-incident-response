import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Incident ────────────────────────────────────────────────────────

VALID_STATUSES = ("open", "investigating", "mitigated", "resolved", "closed")
VALID_SEVERITIES = ("critical", "high", "medium", "low", "info")

STATUS_TRANSITIONS = {
    "open": ("investigating", "mitigated", "resolved", "closed"),
    "investigating": ("mitigated", "resolved", "closed"),
    "mitigated": ("resolved", "closed", "investigating"),
    "resolved": ("closed", "investigating"),
    "closed": ("investigating",),
}


def new_incident(
    affected_service: str,
    environment: str,
    region: str,
    severity: str,
    signal: dict,
) -> dict:
    now = _now()
    return {
        "incident_id": f"INC-{_uuid()[:8].upper()}",
        "created_at": now,
        "updated_at": now,
        "status": "open",
        "severity": severity,
        "affected_service": affected_service,
        "environment": environment,
        "region": region,
        "risk_score": signal.get("risk_score", 0.0),
        "signal_ids": [signal.get("signal_id", "")],
        "signal_count": 1,
        "assigned_analyst": None,
        "description": _build_description(signal),
        "impact_summary": None,
        "tags": _auto_tags(signal),
        "correlation_key": build_correlation_key(signal),
        "first_signal_at": signal.get("detected_at", now),
        "last_signal_at": signal.get("detected_at", now),
    }


def build_correlation_key(signal: dict) -> str:
    parts = [
        signal.get("affected_service") or signal.get("service", "unknown"),
        signal.get("signal_type", "unknown"),
        signal.get("environment", "unknown"),
        signal.get("region", "unknown"),
    ]
    return "|".join(parts)


def _build_description(signal: dict) -> str:
    stype = signal.get("signal_type", "unknown")
    svc = signal.get("affected_service") or signal.get("service", "unknown")
    env = signal.get("environment", "unknown")
    return f"{stype} detected on {svc} in {env}"


def _auto_tags(signal: dict) -> list[str]:
    tags = []
    source = signal.get("source", "")
    if source:
        tags.append(f"source:{source}")
    rule_id = signal.get("rule_id", "")
    if rule_id:
        tags.append(f"rule:{rule_id}")
    event_type = signal.get("event_type", "")
    if event_type:
        tags.append(f"event:{event_type}")
    return tags


# ── Timeline Entry ──────────────────────────────────────────────────

def timeline_entry(
    incident_id: str,
    event_type: str,
    description: str,
    actor: str = "system",
    metadata: dict | None = None,
) -> dict:
    return {
        "entry_id": _uuid(),
        "incident_id": incident_id,
        "timestamp": _now(),
        "event_type": event_type,
        "description": description,
        "actor": actor,
        "metadata": metadata or {},
    }


# ── Analyst Note ────────────────────────────────────────────────────

def analyst_note(
    incident_id: str,
    analyst: str,
    content: str,
) -> dict:
    return {
        "note_id": _uuid(),
        "incident_id": incident_id,
        "analyst": analyst,
        "content": content,
        "created_at": _now(),
    }
