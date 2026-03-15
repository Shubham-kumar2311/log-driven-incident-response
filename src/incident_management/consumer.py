import redis
import json
from config import REDIS_HOST, REDIS_PORT, DETECTION_CHANNEL
from services.incident_service import IncidentService
from publisher import IncidentPublisher


class DetectionConsumer:

    def __init__(self):

        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

        self.service = IncidentService()
        self.publisher = IncidentPublisher()

    def start(self):

        pubsub = self.redis.pubsub()

        pubsub.subscribe(DETECTION_CHANNEL)

        print("Incident Service listening for detection signals...")

        for message in pubsub.listen():

            if message["type"] != "message":
                continue

            data = json.loads(message["data"])

            service = data.get("service")
            error = data.get("error")

            incident = self.service.create_incident(service, error)

            self.publisher.publish(incident)

            print("Incident created:", incident)