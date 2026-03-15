import redis
import json

from pipeline import ProcessingPipeline
from config import USE_REDIS, REDIS_HOST, REDIS_PORT


class ProcessingConsumer:

    def __init__(self):

        self.pipeline = ProcessingPipeline()

        self.last_id = "0"

        if USE_REDIS:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT
            )
        else:
            self.redis_client = None

    def run(self):

        if not USE_REDIS:
            print("Redis disabled — API mode active")
            return

        print("Processing consumer started (Redis mode)")

        while True:

            messages = self.redis_client.xread(
                {"raw_logs": self.last_id},
                block=5000
            )

            for stream, events in messages:

                for msg_id, data in events:

                    try:

                        event = json.loads(data[b"data"])

                        processed = self.pipeline.process(event)

                        if processed:
                            print("Processed:", processed)

                    except Exception as e:

                        print("Processing error:", e)

                    self.last_id = msg_id