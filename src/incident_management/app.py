from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.incident_service import IncidentService

app = FastAPI(
    title="Incident Management Service",
    version="1.0.0"
)

incident_service = IncidentService()


class SignalsPayload(BaseModel):
    signals: list


@app.post("/signals")
def process_signals(payload: SignalsPayload):

    created_incidents = []

    for signal in payload.signals:

        incident = incident_service.create_incident(
            service=signal["service"],
            error=signal["signal_type"]
        )

        created_incidents.append(incident)

    return created_incidents


@app.get("/incidents")
def list_incidents():
    return incident_service.list_incidents()


@app.get("/incident/{incident_id}")
def get_incident(incident_id: str):

    incident = incident_service.get_incident(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident


class StatusUpdate(BaseModel):
    status: str


@app.put("/incident/{incident_id}/status")
def update_status(incident_id: str, body: StatusUpdate):

    incident = incident_service.update_status(
        incident_id,
        body.status
    )

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return incident