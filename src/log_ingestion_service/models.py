from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


class LogEntry(BaseModel):
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

    class Config:
        extra = "allow"

    def normalize(self) -> dict:
        svc = self.service_name or self.service or "unknown"
        lvl = self.log_level or self.level or "INFO"
        evt = self.event_type or self.event or "unknown"
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "service_name": svc,
            "service": svc,
            "category": self.category,
            "log_level": lvl,
            "level": lvl,
            "event_type": evt,
            "event": evt,
            "message": self.message,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "host": self.host,
            "container_id": self.container_id,
            "environment": self.environment or "prod",
            "schema_version": self.schema_version or "1.0",
            "metadata": self.metadata or {},
        }


class BatchLogRequest(BaseModel):
    logs: List[Dict[str, Any]]


class IngestionStats(BaseModel):
    total_logs: int = 0
    logs_per_second: float = 0.0
    services: List[str] = []
    error_count: int = 0
    uptime_seconds: float = 0.0
