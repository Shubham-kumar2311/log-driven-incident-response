from models.incident import Incident
from redis_store import RedisStore


class IncidentService:

    def __init__(self):

        self.store = RedisStore()

    def assign_severity(self, error):

        e = error.lower()

        if "database" in e:
            return "critical"

        if "timeout" in e:
            return "high"

        if "connection" in e:
            return "high"

        if "error" in e:
            return "medium"

        return "low"

    def create_incident(self, service, error):

        severity = self.assign_severity(error)

        incident = Incident(service, error, severity)

        self.store.save_incident(incident.to_dict())

        return incident.to_dict()

    def list_incidents(self):

        return self.store.get_all()

    def get_incident(self, incident_id):

        return self.store.get(incident_id)

    def update_status(self, incident_id, status):

        incident = self.store.get(incident_id)

        if not incident:
            return None

        incident["status"] = status

        self.store.update(incident)

        return incident