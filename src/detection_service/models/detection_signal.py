import uuid
from datetime import datetime


class DetectionSignal:

    def __init__(self, signal_type, severity, service, metadata):

        self.signal_id = str(uuid.uuid4())
        self.signal_type = signal_type
        self.severity = severity
        self.service = service
        self.metadata = metadata
        self.detected_at = datetime.utcnow().isoformat()

    def to_dict(self):

        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "severity": self.severity,
            "service": self.service,
            "metadata": self.metadata,
            "detected_at": self.detected_at
        }