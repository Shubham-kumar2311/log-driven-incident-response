import logging

from incident_manager import IncidentManager
from publisher import publish_incident

logger = logging.getLogger("incident.pipeline")


class IncidentPipeline:

    def __init__(self):
        self.manager = IncidentManager()

    def process(self, signal: dict) -> dict:
        incident = self.manager.process_signal(signal)
        publish_incident(incident)
        return incident

    def process_batch(self, signals: list[dict]) -> list[dict]:
        results = []
        for signal in signals:
            result = self.process(signal)
            results.append(result)
        return results
