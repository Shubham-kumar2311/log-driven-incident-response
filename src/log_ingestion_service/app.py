from fastapi import FastAPI
import threading

from file_watcher import FileWatcher
from raw_event_queue import raw_event_queue

app = FastAPI(title="Log Ingestion Service")

watcher = FileWatcher()


@app.on_event("startup")
def start_watcher():

    thread = threading.Thread(target=watcher.watch, daemon=True)

    thread.start()


@app.get("/health")
def health():

    return {"status": "ok"}


@app.get("/queue-size")
def queue_size():

    return {"raw_event_queue_size": raw_event_queue.qsize()}