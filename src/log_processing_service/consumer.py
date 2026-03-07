import redis
import json
from pipeline import ProcessingPipeline


class ProcessingConsumer:

    def __init__(self):

        self.redis_client = redis.Redis(host="localhost", port=6379)

        self.pipeline = ProcessingPipeline()

        self.last_id = "0"

    def run(self):

        print("Processing consumer started")

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