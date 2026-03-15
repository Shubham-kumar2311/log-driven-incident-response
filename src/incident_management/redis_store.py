import redis
import json
from config import USE_REDIS, REDIS_HOST, REDIS_PORT, INCIDENT_HASH


class RedisStore:

    def __init__(self):

        self.use_redis = USE_REDIS

        if self.use_redis:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
        else:
            self.memory_store = {}

    def save_incident(self, incident):

        if self.use_redis:
            self.client.hset(
                INCIDENT_HASH,
                incident["id"],
                json.dumps(incident)
            )
        else:
            self.memory_store[incident["id"]] = incident

    def get_all(self):

        if self.use_redis:
            incidents = self.client.hgetall(INCIDENT_HASH)

            return [json.loads(v) for v in incidents.values()]

        return list(self.memory_store.values())

    def get(self, incident_id):

        if self.use_redis:
            data = self.client.hget(INCIDENT_HASH, incident_id)

            if data:
                return json.loads(data)

            return None

        return self.memory_store.get(incident_id)

    def update(self, incident):

        if self.use_redis:
            self.client.hset(
                INCIDENT_HASH,
                incident["id"],
                json.dumps(incident)
            )
        else:
            self.memory_store[incident["id"]] = incident