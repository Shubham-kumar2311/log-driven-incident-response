import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import LOG_LEVEL, USE_REDIS, HOST, PORT, ML_MODE
from detection_store import DetectionStore
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
store = DetectionStore()


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
        "ml_mode": ML_MODE,
        "ml_enabled": ML_MODE in ("runtime", "hybrid") or bool(pipeline.ml_client.url),
        "runtime_ml": pipeline.ml_client.runtime_snapshot(),
    }


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()


@app.post("/feedback")
def submit_feedback(payload: dict):
    log_id = payload.get("log_id")
    if not log_id:
        return {"status": "error", "message": "log_id is required"}

    feedback = store.save_feedback(
        log_id=log_id,
        is_false_positive=bool(payload.get("is_false_positive", False)),
        notes=payload.get("notes", ""),
    )
    return {"status": "ok", "feedback": feedback}


@app.get("/training/labeled-data")
def labeled_data():
    samples = store.get_labeled_anomaly_samples()
    return {"count": len(samples), "samples": samples}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)