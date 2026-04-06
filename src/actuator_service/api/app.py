"""
Actuator Service - FastAPI Application.

Provides REST API for:
- Direct action execution
- Execution history and monitoring
- Health and metrics endpoints
- Monitoring dashboard
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0].rsplit("\\", 2)[0])

from config import USE_REDIS, LOG_LEVEL
from pipeline import pipeline, handle_response_event
from messaging.consumer import consumer
from messaging.publisher import publisher
from executor.action_executor import executor
from ui.dashboard import DASHBOARD_HTML

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    """Request model for action execution."""
    incident_id: str = Field(..., description="Incident ID")
    action: str = Field(..., description="Action name to execute")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional parameters for the action"
    )


class ExecuteResponse(BaseModel):
    """Response model for action execution."""
    incident_id: str
    action: str
    execution_status: str
    output: str
    executed_at: str
    duration_ms: float
    retries: int
    mode: str
    details: Dict[str, Any]


class BatchExecuteRequest(BaseModel):
    """Request for batch action execution."""
    actions: List[ExecuteRequest]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    uptime_seconds: float
    registered_actions: List[str]
    action_count: int
    redis_connected: bool
    use_redis: bool
    executions: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response."""
    total_executions: int
    success_count: int
    failed_count: int
    timeout_count: int
    success_rate_percent: float
    uptime_seconds: float
    executions_per_minute: float


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan Management
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Actuator Service...")
    logger.info(f"Redis mode: {'enabled' if USE_REDIS else 'disabled'}")

    # Start Redis consumer if enabled
    consumer_task = None
    if USE_REDIS:
        consumer.set_handler(handle_response_event)
        consumer_task = asyncio.create_task(consumer.start())
        logger.info("Redis consumer started")

    logger.info(f"Registered actions: {executor.get_registered_actions()}")

    yield

    # Shutdown
    logger.info("Shutting down Actuator Service...")
    consumer.stop()
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    consumer.close()
    publisher.close()
    logger.info("Shutdown complete")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Actuator Service",
    description="Execution layer for incident response actions",
    version="1.0.0",
    lifespan=lifespan
)


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/execute", response_model=ExecuteResponse)
async def execute_action(request: ExecuteRequest):
    """
    Execute a single action.

    This endpoint triggers the execution of a remediation action.
    """
    logger.info(f"API execute request: action={request.action}, incident={request.incident_id}")

    result = await pipeline.execute_direct(
        action=request.action,
        incident_id=request.incident_id,
        parameters=request.parameters
    )

    return ExecuteResponse(**result.to_dict())


@app.post("/execute/batch", response_model=List[ExecuteResponse])
async def execute_batch(request: BatchExecuteRequest):
    """
    Execute multiple actions in parallel.
    """
    logger.info(f"API batch execute request: {len(request.actions)} actions")

    tasks = [
        pipeline.execute_direct(
            action=action.action,
            incident_id=action.incident_id,
            parameters=action.parameters
        )
        for action in request.actions
    ]

    results = await asyncio.gather(*tasks)
    return [ExecuteResponse(**r.to_dict()) for r in results]


@app.get("/history")
async def get_history(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent execution history.

    Args:
        limit: Maximum number of results (default 50)
    """
    history = pipeline.history.get_recent(limit)
    return {
        "count": len(history),
        "executions": history
    }


@app.get("/actions")
async def get_actions() -> Dict[str, Any]:
    """
    Get list of available actions.
    """
    return {
        "actions": executor.get_registered_actions(),
        "count": len(executor.get_registered_actions())
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    """
    health = pipeline.get_health()
    return HealthResponse(
        **health,
        redis_connected=consumer.is_connected(),
        use_redis=USE_REDIS
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get execution metrics.
    """
    return MetricsResponse(**pipeline.get_metrics())


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """
    Serve the monitoring dashboard.
    """
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/dashboard-data")
async def dashboard_data() -> Dict[str, Any]:
    """
    API endpoint for dashboard data polling.
    """
    history = pipeline.history.get_recent(50)
    metrics = pipeline.get_metrics()

    return {
        "executions": history,
        "metrics": metrics,
        "redis_connected": consumer.is_connected(),
        "use_redis": USE_REDIS,
        "registered_actions": executor.get_registered_actions()
    }
