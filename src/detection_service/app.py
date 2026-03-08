from fastapi import FastAPI
import threading

from config import USE_REDIS
from consumer import DetectionConsumer
from pipeline import DetectionPipeline

app = FastAPI(title="Detection Service")

pipeline = DetectionPipeline()


if USE_REDIS:

    consumer = DetectionConsumer()

    @app.on_event("startup")
    def start_detection():

        thread = threading.Thread(
            target=consumer.run,
            daemon=True
        )

        thread.start()

        print("Detection running in REDIS mode")

else:

    print("Detection running in API mode")


@app.post("/detect")
def detect(event: dict):

    signals = pipeline.process(event)

    return {"signals": signals}


@app.get("/health")
def health():

    return {
        "status": "detection service running",
        "mode": "redis" if USE_REDIS else "api"
    }