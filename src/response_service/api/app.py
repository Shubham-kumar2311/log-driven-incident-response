import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, "..")

from config import USE_REDIS, LOG_LEVEL
from db.mongo_client import mongo_client
from repository.playbook_repository import PlaybookRepository
from engine.playbook_engine import PlaybookEngine
from messaging.publisher import publisher
from pipeline import pipeline
from ui.dashboard import DASHBOARD_HTML

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Pydantic Models ---

class PlaybookCreate(BaseModel):
    signal_type: str = Field(..., description="Signal type this playbook handles")
    action: str = Field(..., description="Action to execute")
    description: str = Field("", description="Description of the playbook")
    enabled: bool = Field(True, description="Whether playbook is enabled")
    priority: int = Field(1, description="Priority (lower = higher priority)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class PlaybookUpdate(BaseModel):
    signal_type: Optional[str] = None
    action: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None


class PlaybookToggle(BaseModel):
    enabled: bool


class IncidentInput(BaseModel):
    id: Optional[str] = Field(None, description="Incident ID")
    signal_type: Optional[str] = Field(None, alias="error", description="Signal type / error type")
    error: Optional[str] = Field(None, description="Error type (alias for signal_type)")
    service: Optional[str] = Field(None, description="Service name")
    source_ip: Optional[str] = Field(None, description="Source IP")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")

    class Config:
        populate_by_name = True


class SimulateRequest(BaseModel):
    signal_type: str = Field(..., description="Signal type to simulate")
    incident_data: Optional[Dict[str, Any]] = Field(None, description="Optional incident data")


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Response Service...")

    # Connect to MongoDB
    try:
        mongo_client.connect()
        logger.info("MongoDB connected")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

    # Seed default playbooks
    try:
        repo = PlaybookRepository()
        repo.seed_default_playbooks()
    except Exception as e:
        logger.warning(f"Could not seed playbooks: {e}")

    # Start Redis consumer if enabled
    consumer_task = None
    if USE_REDIS:
        logger.info("Starting Redis consumer...")
        consumer_task = asyncio.create_task(pipeline.start())

    yield

    # Cleanup
    logger.info("Shutting down Response Service...")
    if consumer_task:
        pipeline.stop()
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    publisher.close()
    mongo_client.close()


# --- FastAPI App ---

app = FastAPI(
    title="Response / Playbook Service",
    description="Automated incident response with dynamic playbooks",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repository and engine instances
repository = PlaybookRepository()
engine = PlaybookEngine(repository)


# --- Health Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "response_service",
        "mode": "redis" if USE_REDIS else "api",
        "mongodb_connected": mongo_client.is_connected(),
        "redis_enabled": USE_REDIS,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serves dashboard."""
    return DASHBOARD_HTML


# --- Playbook CRUD Endpoints ---

@app.get("/playbooks", response_model=List[Dict[str, Any]])
async def get_all_playbooks():
    """Get all playbooks."""
    return repository.get_all_playbooks()


@app.get("/playbooks/{playbook_id}")
async def get_playbook(playbook_id: str):
    """Get a specific playbook by ID."""
    playbook = repository.get_playbook_by_id(playbook_id)
    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook not found: {playbook_id}"
        )
    return playbook


@app.post("/playbooks", status_code=status.HTTP_201_CREATED)
async def create_playbook(playbook: PlaybookCreate):
    """Create a new playbook."""
    # Check for duplicate signal_type
    existing = repository.get_playbook(playbook.signal_type)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Playbook already exists for signal_type: {playbook.signal_type}"
        )

    result = repository.create_playbook(playbook.model_dump())
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create playbook"
        )
    return result


@app.put("/playbooks/{playbook_id}")
async def update_playbook(playbook_id: str, playbook: PlaybookUpdate):
    """Update an existing playbook."""
    # Filter out None values
    update_data = {k: v for k, v in playbook.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )

    result = repository.update_playbook(playbook_id, update_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook not found: {playbook_id}"
        )
    return result


@app.patch("/playbooks/{playbook_id}/toggle")
async def toggle_playbook(playbook_id: str, toggle: PlaybookToggle):
    """Enable or disable a playbook."""
    result = repository.toggle_playbook(playbook_id, toggle.enabled)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook not found: {playbook_id}"
        )
    return result


@app.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(playbook_id: str):
    """Delete a playbook."""
    success = repository.delete_playbook(playbook_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook not found: {playbook_id}"
        )
    return None


# --- Response Endpoints ---

@app.post("/simulate-response")
async def simulate_response(incident: IncidentInput):
    """
    Process an incident and return the response.
    This is the main API endpoint for incident processing.
    """
    # Build incident dict
    incident_data = {
        "id": incident.id or f"api-{datetime.utcnow().timestamp()}",
        "signal_type": incident.signal_type or incident.error,
        "error": incident.error or incident.signal_type,
        "service": incident.service,
        "source_ip": incident.source_ip,
        "details": incident.details
    }

    # Remove None values
    incident_data = {k: v for k, v in incident_data.items() if v is not None}

    response = await pipeline.process_single(incident_data)
    return response


@app.post("/simulate")
async def simulate_playbook(request: SimulateRequest):
    """
    Simulate playbook execution for a signal type.
    Useful for testing playbooks without real incidents.
    """
    response = await engine.simulate(
        signal_type=request.signal_type,
        incident_data=request.incident_data
    )
    return response


@app.get("/actions")
async def list_available_actions():
    """List all available actions that can be used in playbooks."""
    return {
        "actions": [
            {
                "name": "restart_database",
                "description": "Restart the database service",
                "parameters": ["graceful", "timeout"]
            },
            {
                "name": "restart_api",
                "description": "Restart API servers with rolling deployment",
                "parameters": ["rolling", "batch_size"]
            },
            {
                "name": "lock_accounts",
                "description": "Lock accounts from suspicious IPs",
                "parameters": ["lock_duration_minutes"]
            },
            {
                "name": "rollback_deployment",
                "description": "Rollback a failed deployment",
                "parameters": ["keep_logs"]
            },
            {
                "name": "scale_service",
                "description": "Scale up service instances",
                "parameters": ["scale_factor", "max_instances"]
            },
            {
                "name": "restart_cache",
                "description": "Restart cache service",
                "parameters": ["flush_on_restart"]
            },
            {
                "name": "notify_oncall",
                "description": "Notify on-call engineer",
                "parameters": ["channel"]
            }
        ]
    }
