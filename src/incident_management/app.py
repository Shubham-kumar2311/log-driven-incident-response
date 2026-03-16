import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api.incident_routes import init_routes, router as incident_router
from config import LOG_LEVEL, USE_REDIS
from consumer import DetectionConsumer
from incident_manager import IncidentManager
from incident_store import IncidentStore
from logger import setup_logging
from metrics import metrics
from ui.dashboard import DASHBOARD_HTML

setup_logging(LOG_LEVEL)

_manager = IncidentManager()
_store = _manager.store
init_routes(_manager, _store)


@asynccontextmanager
async def lifespan(application: FastAPI):
    if USE_REDIS:
        consumer = DetectionConsumer()
        t = threading.Thread(target=consumer.run, daemon=True)
        t.start()
    yield


app = FastAPI(
    title="Incident Management Service",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(incident_router)


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "incident-management",
        "mode": "redis-stream" if USE_REDIS else "http-api",
        "incidents_total": _store.get_incident_count(),
    }


@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()
