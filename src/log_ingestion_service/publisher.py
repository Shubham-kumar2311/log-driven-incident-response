import json
import requests
import redis

from config import USE_REDIS, REDIS_HOST, REDIS_PORT, PROCESS_API


redis_client = None

if USE_REDIS:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )


def publish_event(event: dict):

    try:

        if USE_REDIS and redis_client:

            redis_client.xadd(
                "raw_logs",
                {"data": json.dumps(event)}
            )

        else:

            requests.post(
                PROCESS_API,
                json=event,
                timeout=2
            )

    except Exception as e:
        print(f"[PUBLISH ERROR] {e}")