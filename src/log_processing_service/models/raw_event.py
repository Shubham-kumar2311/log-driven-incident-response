from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any


class RawEvent(BaseModel):
    """Schema matching ingestion service normalized output."""
    model_config = {"extra": "allow"}

    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    service_name: Optional[str] = None
    service: Optional[str] = None
    category: Optional[str] = None
    log_level: Optional[str] = None
    level: Optional[str] = None
    event_type: Optional[str] = None
    event: Optional[str] = None
    message: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    host: Optional[str] = None
    container_id: Optional[str] = None
    environment: Optional[str] = None
    schema_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ingested_at: Optional[str] = None

    def resolved_service(self) -> str:
        return self.service_name or self.service or "unknown"

    def resolved_level(self) -> str:
        return self.log_level or self.level or "INFO"

    def resolved_event_type(self) -> str:
        return self.event_type or self.event or "unknown"

    @field_validator("log_level", "level", mode="before")
    @classmethod
    def upper_level(cls, v):
        return v.upper() if isinstance(v, str) else v