from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class ProcessedEvent(BaseModel):
    """Output schema sent to the detection service."""
    event_id: str
    timestamp: str
    ingested_at: Optional[str] = None
    processed_at: str

    # Source identification
    service_name: str
    category: Optional[str] = None
    environment: str = "production"

    # Classification
    log_level: str
    event_type: str
    normalized_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO

    # Content
    message: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    # Enrichment
    region: str = "us-east-1"
    cluster: str = "prod-cluster"
    risk_score: float = 0.0
    tags: List[str] = []

    # Features for detection
    features: Dict[str, Any] = {}

    # Original payload
    metadata: Dict[str, Any] = {}