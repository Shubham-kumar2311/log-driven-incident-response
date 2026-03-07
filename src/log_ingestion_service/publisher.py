import redis
import json
import os

REDIS_ENABLED = os.getenv("USE_REDIS", "true") == "true"

if REDIS_ENABLED:
    redis_client = redis.Redis(host="localhost", port=6379)


def publish_event(event):

    if REDIS_ENABLED:

        redis_client.xadd(
            "raw_logs",
            {"data": json.dumps(event)}
        )

    else:
        import requests
        requests.post(
            "http://localhost:8002/process",
            json=event
        )