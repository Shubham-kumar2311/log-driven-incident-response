from dataclasses import dataclass
from typing import Dict


@dataclass
class NormalizedEvent:
    event_id: str
    service_name: str
    normalized_type: str
    severity: str
    timestamp: str
    metadata: Dict
    features: Dict