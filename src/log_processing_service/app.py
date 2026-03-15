from fastapi import FastAPI
import threading

from consumer import ProcessingConsumer
from pipeline import ProcessingPipeline
from publisher import publish
from queues import processed_event_queue
from config import USE_REDIS

app = FastAPI(title="Log Processing Service")

consumer = ProcessingConsumer()
pipeline = ProcessingPipeline()


@app.on_event("startup")
def start_processing():

    if USE_REDIS:

        thread = threading.Thread(
            target=consumer.run,
            daemon=True
        )

        thread.start()

        print("Processing consumer started (Redis mode)")

    else:

        print("Processing running in API mode")


@app.post("/process")
def process_event(event: dict):

    processed = pipeline.process(event)

    if processed:
        publish(processed)

        return {
            "status": "processed",
            "processed_event": processed
        }

    return {
        "status": "dropped"
    }


@app.get("/health")
def health():

    return {"status": "processing service running"}


@app.get("/processed-queue-size")
def queue_size():

    return {
        "processed_event_queue_size": processed_event_queue.qsize()
    }