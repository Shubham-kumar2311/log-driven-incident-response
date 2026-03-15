import uuid
from datetime import datetime


class Incident:

    def __init__(self, service, error, severity):

        self.id = str(uuid.uuid4())
        self.service = service
        self.error = error
        self.severity = severity
        self.status = "open"

        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self):

        return {
            "id": self.id,
            "service": self.service,
            "error": self.error,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at
        }