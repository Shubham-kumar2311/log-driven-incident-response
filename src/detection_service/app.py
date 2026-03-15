import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import LOG_LEVEL, USE_REDIS
from logger import setup_logging
from metrics import metrics
from pipeline import DetectionPipeline
from publisher import publish_signals

# ── Bootstrap structured logging before anything else ───────────────
setup_logging(LOG_LEVEL)

import logging  # noqa: E402 (must come after setup_logging)

log = logging.getLogger("detection.app")


# ── Lifespan (modern FastAPI startup/shutdown) ──────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    log.info("Detection service starting (mode=%s)", "redis" if USE_REDIS else "api")

    if USE_REDIS:
        from consumer import DetectionConsumer

        consumer = DetectionConsumer()
        thread = threading.Thread(target=consumer.run, daemon=True, name="detection-consumer")
        thread.start()
        log.info("Redis stream consumer started")

    yield
    log.info("Detection service shutting down")


app = FastAPI(title="Detection Service", version="2.0.0", lifespan=lifespan)
pipeline = DetectionPipeline()


# ── Endpoints ───────────────────────────────────────────────────────

@app.post("/detect")
def detect(event: dict):
    """Run a single event through the detection pipeline."""
    signals = pipeline.process(event)

    if signals:
        publish_signals(signals)

    return {"signals": signals}


@app.post("/detect/batch")
def detect_batch(payload: dict):
    """Run a batch of events through the detection pipeline."""
    events = payload.get("events", [])
    signals = pipeline.process_batch(events)

    if signals:
        publish_signals(signals)

    return {"signals": signals, "events_received": len(events)}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "detection-service",
        "mode": "redis" if USE_REDIS else "api",
        "rules_loaded": len(pipeline.rule_engine.rules),
        "anomaly_detectors": len(pipeline.anomaly_engine.detectors),
    }


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()