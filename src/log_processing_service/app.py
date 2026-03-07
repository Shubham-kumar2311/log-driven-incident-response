from fastapi import FastAPI
import threading

from consumer import ProcessingConsumer
from queues import processed_event_queue

app = FastAPI(title="Log Processing Service")

consumer = ProcessingConsumer()


@app.on_event("startup")
def start_processing():
    """
    Start the background consumer when service starts.
    """

    thread = threading.Thread(
        target=consumer.run,
        daemon=True
    )

    thread.start()

    print("Processing consumer started")


@app.get("/health")
def health():
    return {
        "status": "processing service running"
    }


@app.get("/processed-queue-size")
def queue_size():
    return {
        "processed_event_queue_size": processed_event_queue.qsize()
    }