import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import USE_REDIS, LOG_LEVEL
from consumer import ProcessingConsumer
from pipeline import ProcessingPipeline
from publisher import publish_event, get_local_queue

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("processing.app")

# ── Shared instances ─────────────────────────────────────
pipeline = ProcessingPipeline()
consumer = ProcessingConsumer(pipeline=pipeline)


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    if USE_REDIS:
        t = threading.Thread(target=consumer.run, daemon=True)
        t.start()
        logger.info("Redis consumer thread started")
    else:
        logger.info("Running in API-only mode")
    yield
    consumer.stop()
    logger.info("Processing service shutting down")


app = FastAPI(title="Log Processing Service", lifespan=lifespan)


# ── Endpoints ────────────────────────────────────────────
@app.post("/process")
async def process_event_endpoint(request: Request):
    """Accept a single raw event via HTTP (used when Redis is disabled)."""
    event = await request.json()
    processed = pipeline.process(event)

    if processed:
        publish_event(processed)
        return {"status": "processed", "processed_event": processed}

    return {"status": "dropped"}


@app.post("/process/batch")
async def process_batch_endpoint(request: Request):
    """Accept a batch of raw events."""
    events = await request.json()
    if not isinstance(events, list):
        return JSONResponse(status_code=400, content={"error": "Expected a JSON array"})

    results = pipeline.process_batch(events)
    for r in results:
        publish_event(r)

    return {
        "status": "processed",
        "total": len(events),
        "processed": len(results),
        "dropped": len(events) - len(results),
    }


@app.get("/health")
def health():
    return {"status": "processing service running"}


@app.get("/metrics")
def metrics():
    """Pipeline processing metrics."""
    return pipeline.get_metrics()


@app.get("/processed-queue-size")
def queue_size():
    return {"processed_event_queue_size": get_local_queue().qsize()}
