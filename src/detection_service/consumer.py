import redis
import json

from config import REDIS_HOST, REDIS_PORT, INPUT_STREAM
from pipeline import DetectionPipeline
from publisher import publish_signal


class DetectionConsumer:

    def __init__(self):

        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.pipeline = DetectionPipeline()
        self.last_id = "0"

    def run(self):

        print("Detection consumer started")

        while True:

            messages = self.redis.xread(
                {INPUT_STREAM: self.last_id},
                block=5000
            )

            for stream, events in messages:

                for msg_id, data in events:

                    event = json.loads(data[b"data"])

                    signals = self.pipeline.process(event)

                    for signal in signals:
                        publish_signal(signal)

                    self.last_id = msg_id