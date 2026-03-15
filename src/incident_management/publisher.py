import redis
import json
from config import REDIS_HOST, REDIS_PORT, INCIDENT_CHANNEL


class IncidentPublisher:

    def __init__(self):

        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

    def publish(self, incident):

        self.redis.publish(
            INCIDENT_CHANNEL,
            json.dumps(incident)
        )