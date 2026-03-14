from dataclasses import dataclass
from typing import Dict


@dataclass
class RawEvent:
    event_id: str
    service_name: str
    timestamp: str
    log_level: str
    event_type: str
    message: str
    metadata: Dict
    trace_id: str