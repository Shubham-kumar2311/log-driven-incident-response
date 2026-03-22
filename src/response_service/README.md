# Response / Playbook Service

Automated incident response with dynamic playbooks stored in MongoDB.

## Architecture

```
incident_events (Redis) → Consumer → Playbook Engine → Action Executor → response_events (Redis)
                                            ↓
                                     MongoDB (playbooks)
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- MongoDB running on `localhost:27017`
- Redis running on `localhost:6379` (optional, for event mode)
- Node.js 18+ (for frontend)

### 2. Start MongoDB

```bash
# Docker
docker run -d -p 27017:27017 --name mongodb mongo:7

# Or use local installation
mongod --dbpath /data/db
```

### 3. Start Redis (Optional)

```bash
# Docker
docker run -d -p 6379:6379 --name redis redis:7

# Or use local installation
redis-server
```

### 4. Start Backend

```bash
cd src/response_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start the service (API mode + embedded dashboard)
python -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload

# Or with Redis consumer mode
USE_REDIS=true python -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

Dashboard available at: http://localhost:8002

### 5. Access Backend & Dashboard

The backend serves the dashboard at the root URL:

```bash
# Backend API + Dashboard: http://localhost:8002
open http://localhost:8002
```

API Documentation is available at:
```bash
# API Docs: http://localhost:8002/docs
open http://localhost:8002/docs
```

**Optional: Use separate React dev server** (for frontend development)

```bash
cd src/response_service/ui

# Install dependencies
npm install

# Start Vite dev server (proxies to backend)
npm run dev  # Runs on port 3000, proxies backend to 8004

# Or with custom backend port
BACKEND_PORT=8002 npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/playbooks` | List all playbooks |
| GET | `/playbooks/{id}` | Get playbook by ID |
| POST | `/playbooks` | Create playbook |
| PUT | `/playbooks/{id}` | Update playbook |
| PATCH | `/playbooks/{id}/toggle` | Enable/disable playbook |
| DELETE | `/playbooks/{id}` | Delete playbook |
| POST | `/simulate-response` | Process incident |
| POST | `/simulate` | Test playbook |
| GET | `/actions` | List available actions |

## Example API Usage

Set `PORT=8002` (or your backend port) and use:

### Create Playbook

```bash
curl -X POST http://localhost:$PORT/playbooks \
  -H "Content-Type: application/json" \
  -d '{
    "signal_type": "CPU_SPIKE",
    "action": "scale_service",
    "description": "Scale service when CPU spikes",
    "enabled": true,
    "parameters": {"scale_factor": 2}
  }'
```

### Simulate Incident Response

```bash
curl -X POST http://localhost:$PORT/simulate-response \
  -H "Content-Type: application/json" \
  -d '{
    "id": "inc-001",
    "error": "DB_SLOW_QUERY",
    "service": "postgres",
    "details": {"latency_ms": 5000}
  }'
```

### Toggle Playbook

```bash
curl -X PATCH http://localhost:$PORT/playbooks/{id}/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## MongoDB Schema

Collection: `playbooks`

```json
{
  "_id": "ObjectId",
  "signal_type": "DB_SLOW_QUERY",
  "action": "restart_database",
  "description": "Restart DB when latency exceeds threshold",
  "enabled": true,
  "priority": 1,
  "parameters": {
    "graceful": true,
    "timeout": 30
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Default Playbooks

On first start, the service seeds these playbooks:

| Signal Type | Action | Description |
|-------------|--------|-------------|
| DB_SLOW_QUERY | restart_database | Restart database on slow queries |
| HTTP_ERROR_SPIKE | restart_api | Restart API on 5xx errors |
| AUTH_FAILURE_SPIKE | lock_accounts | Lock accounts on brute force |
| DEPLOYMENT_FAILURE | rollback_deployment | Rollback failed deployments |
| HIGH_LATENCY | scale_service | Scale on high latency (disabled) |
| CACHE_ERROR | restart_cache | Restart cache on errors |

## Available Actions

| Action | Parameters |
|--------|------------|
| restart_database | graceful, timeout |
| restart_api | rolling, batch_size |
| lock_accounts | lock_duration_minutes |
| rollback_deployment | keep_logs |
| scale_service | scale_factor, max_instances |
| restart_cache | flush_on_restart |
| notify_oncall | channel |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| USE_REDIS | false | Enable Redis consumer mode |
| REDIS_HOST | localhost | Redis host |
| REDIS_PORT | 6379 | Redis port |
| MONGO_URI | mongodb://localhost:27017 | MongoDB connection |
| MONGO_DB | incident_response | Database name |
| ACTION_TIMEOUT_SECONDS | 30 | Action execution timeout |
| ACTION_MAX_RETRIES | 3 | Max retry attempts |
| LOG_LEVEL | INFO | Logging level |

## Folder Structure

```
response_service/
├── api/
│   └── app.py           # FastAPI application
├── db/
│   └── mongo_client.py  # MongoDB client
├── repository/
│   └── playbook_repository.py  # CRUD operations
├── engine/
│   └── playbook_engine.py      # Matching & execution
├── actions/
│   └── executor.py      # Action handlers
├── messaging/
│   ├── consumer.py      # Redis consumer
│   └── publisher.py     # Redis publisher
├── ui/                  # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── config.py
├── pipeline.py
├── requirements.txt
└── .env
```

## Integration

### Upstream (Incident Management)

Send incidents to this service via:
- **Redis Stream**: `incident_events` (when USE_REDIS=true)
- **HTTP POST**: `/simulate-response`

### Downstream

Response events published to:
- **Redis Stream**: `response_events` (when USE_REDIS=true)

## Production Deployment

1. Use proper MongoDB authentication
2. Enable Redis mode for event-driven processing
3. Use environment variables for configuration
4. Set up monitoring on `/health` endpoint
5. Use process manager (systemd, PM2) for reliability
