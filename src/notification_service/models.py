from pydantic import BaseModel


class Incident(BaseModel):

    incident_id: str
    service: str
    severity: str
    event_type: str
    timestamp: str
    message: str | None = None
    receiver_email: str | None = None
    reciever_email: str | None = None