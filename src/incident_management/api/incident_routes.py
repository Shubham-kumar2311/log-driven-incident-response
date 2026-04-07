import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from incident_manager import IncidentManager
from incident_store import IncidentStore
from models.incident_model import VALID_STATUSES, STATUS_TRANSITIONS

logger = logging.getLogger("incident.api")

router = APIRouter()

_manager: IncidentManager | None = None
_store: IncidentStore | None = None


def init_routes(manager: IncidentManager, store: IncidentStore):
    global _manager, _store
    _manager = manager
    _store = store


# ── Request Models ──────────────────────────────────────────────────

class SignalsPayload(BaseModel):
    signals: list[dict]


class StatusUpdate(BaseModel):
    status: str
    actor: str = "system"


class AssignRequest(BaseModel):
    analyst: str


class NoteRequest(BaseModel):
    analyst: str
    content: str


class ResponseActionRequest(BaseModel):
    action_type: str
    actor: str = "system"
    details: str = ""


# ── Signal Ingestion ────────────────────────────────────────────────

@router.post("/signals")
def ingest_signals(payload: SignalsPayload):
    print(f"Received {len(payload.signals)} signals for processing")
    results = []
    for signal in payload.signals:
        incident = _manager.process_signal(signal)
        results.append(incident)
    return {"incidents": results, "count": len(results)}


# ── Incident CRUD ───────────────────────────────────────────────────

@router.get("/incidents")
def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    affected_service: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
):
    filters = {}
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity
    if affected_service:
        filters["affected_service"] = affected_service
    if environment:
        filters["environment"] = environment

    incidents = _store.list_incidents(filters)
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/incidents/active")
def list_active_incidents():
    incidents = _store.list_active_incidents()
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    timeline = _store.get_timeline(incident_id)
    notes = _store.get_notes(incident_id)
    actions = _store.get_actions(incident_id)

    return {
        "incident": incident,
        "timeline": timeline,
        "notes": notes,
        "actions": actions,
    }


# ── Lifecycle ───────────────────────────────────────────────────────

@router.patch("/incidents/{incident_id}/status")
def update_status(incident_id: str, body: StatusUpdate):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    current = incident["status"]
    new = body.status.lower()

    if new not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")

    allowed = STATUS_TRANSITIONS.get(current, ())
    if new not in allowed and new != current:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{new}'. Allowed: {allowed}",
        )

    from metrics import metrics
    metrics.record_status_change(current, new)

    updated = _store.update_status(incident_id, new, actor=body.actor)
    return updated


# ── Assignment ──────────────────────────────────────────────────────

@router.post("/incidents/{incident_id}/assign")
def assign_incident(incident_id: str, body: AssignRequest):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    updated = _store.assign_analyst(incident_id, body.analyst)
    return updated


# ── Notes ───────────────────────────────────────────────────────────

@router.post("/incidents/{incident_id}/notes")
def add_note(incident_id: str, body: NoteRequest):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    note = _store.add_note(incident_id, body.analyst, body.content)
    return note


@router.get("/incidents/{incident_id}/notes")
def get_notes(incident_id: str):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _store.get_notes(incident_id)


# ── Timeline ────────────────────────────────────────────────────────

@router.get("/incidents/{incident_id}/timeline")
def get_timeline(incident_id: str):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _store.get_timeline(incident_id)


# ── Response Actions ────────────────────────────────────────────────

@router.post("/incidents/{incident_id}/response")
def trigger_response(incident_id: str, body: ResponseActionRequest):
    incident = _store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    _store._add_action(incident_id, body.actor, body.action_type, body.details)
    _store._add_timeline(
        incident_id,
        "response_action",
        f"Response action triggered: {body.action_type} — {body.details}",
        actor=body.actor,
    )

    logger.info(
        "Response action triggered",
        extra={"incident_id": incident_id, "action": body.action_type},
    )
    return {"status": "ok", "action_type": body.action_type, "incident_id": incident_id}
