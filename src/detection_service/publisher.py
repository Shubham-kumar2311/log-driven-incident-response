import redis
import json

from config import REDIS_HOST, REDIS_PORT, OUTPUT_STREAM

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


def publish_signal(signal):

    redis_client.xadd(
        OUTPUT_STREAM,
        {"data": json.dumps(signal)}
    )

    print("Signal generated:", signal)