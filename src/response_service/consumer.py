import redis
import json

from config import USE_REDIS, REDIS_HOST, REDIS_PORT, INCIDENT_CHANNEL
from playbook_engine import PlaybookEngine
from publisher import ResponsePublisher


class IncidentConsumer:

    def __init__(self):

        self.engine = PlaybookEngine()
        self.publisher = ResponsePublisher()

        if USE_REDIS:
            self.redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )

    def start(self):

        if not USE_REDIS:
            print("Redis disabled — consumer not started")
            return

        pubsub = self.redis.pubsub()

        pubsub.subscribe(INCIDENT_CHANNEL)

        print("Listening for incident events...")

        for message in pubsub.listen():

            if message["type"] != "message":
                continue

            incident = json.loads(message["data"])

            response = self.engine.execute(incident)

            self.publisher.publish(response)