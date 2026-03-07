import redis
import json
from pipeline import ProcessingPipeline

redis_client = redis.Redis(host="localhost", port=6379)

pipeline = ProcessingPipeline()

last_id = "0"


def consume():

    global last_id

    while True:

        messages = redis_client.xread(
            {"raw_logs": last_id},
            block=5000
        )

        for stream, events in messages:

            for msg_id, data in events:

                event = json.loads(data[b"data"])

                processed = pipeline.process(event)

                if processed:
                    print("Processed:", processed)

                last_id = msg_id