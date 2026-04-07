import sys
import queue
import logging
import threading

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from client_auth_middleware import AuthMiddlewareASGI

from config import MAX_BATCH_SIZE, CORS_ORIGINS, HOST, PORT
from file_watcher import FileWatcher
from processor import process_log, process_batch
from publisher import publish_event
from stats_tracker import stats
from event_queue import get_queue, enqueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ingestion")

app = FastAPI(title="Log Ingestion Service", version="2.0.0")


# CORS for authentication
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware - require ANALYST role
app.add_middleware(AuthMiddlewareASGI, required_role="USER")

watcher = FileWatcher()


def _publisher_worker():
    """Background thread: drains the publish queue and forwards events downstream."""
    q = get_queue()
    while True:
        try:
            event = q.get(timeout=1.0)
        except queue.Empty:
            continue
        try:
            publish_event(event)
        except Exception as e:
            logger.error("Publisher worker error: %s", e)
        finally:
            q.task_done()


@app.on_event("startup")
def startup():
    threading.Thread(target=watcher.watch, daemon=True, name="file-watcher").start()
    threading.Thread(target=_publisher_worker, daemon=True, name="publisher").start()
    logger.info("Ingestion service started (file-watcher + publisher threads running)")


# --- Health & Metrics ---

@app.get("/health")
def health():
    return {"status": "ok", "service": "log-ingestion-service"}


@app.get("/metrics")
def metrics():
    s = stats.get_stats()
    return {
        "total_logs_ingested": s["total_logs"],
        "logs_per_second": s["logs_per_second"],
        "active_services": len(s["services"]),
        "error_count": s["error_count"],
        "uptime_seconds": s["uptime_seconds"],
        "queue_size": get_queue().qsize(),
    }


# --- Log Ingestion API ---

@app.post("/logs")
async def ingest_single_log(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    normalized = process_log(body)
    if not normalized:
        return JSONResponse(status_code=422, content={"error": "Log validation failed"})

    enqueue(normalized)
    return {"status": "accepted", "event_id": normalized.get("event_id")}


@app.post("/logs/batch")
async def ingest_batch(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    logs = body.get("logs", [])
    if not logs:
        return JSONResponse(status_code=400, content={"error": "Empty batch"})

    if len(logs) > MAX_BATCH_SIZE:
        return JSONResponse(
            status_code=413,
            content={"error": f"Batch too large. Max {MAX_BATCH_SIZE} logs per request."}
        )

    results = process_batch(logs)
    queued = sum(1 for r in results if enqueue(r))
    return {
        "status": "accepted",
        "received": len(logs),
        "processed": len(results),
        "queued": queued,
    }


# --- Dashboard API ---

@app.get("/ingestion/stats")
def ingestion_stats():
    s = stats.get_stats()
    s["queue_size"] = get_queue().qsize()
    return s


@app.get("/ingestion/recent-logs")
def recent_logs(limit: int = 20):
    limit = min(limit, 50)
    return {"logs": stats.get_recent_logs(limit)}


# --- Dashboard UI ---

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ingestion Dashboard</title>
<style>
    :root {
        --bg: #0f1117;
        --panel: #161b22;
        --border: #30363d;
        --text: #e1e4e8;
        --muted: #8b949e;
        --accent: #58a6ff;
        --ok: #3fb950;
        --warn: #d29922;
        --err: #f85149;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: radial-gradient(circle at 20% 0%, #151d2e 0%, var(--bg) 52%);
        color: var(--text);
        padding: 20px;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 { font-size: 1.5rem; margin-bottom: 16px; color: var(--accent); }
    h2 {
        font-size: 1rem;
        margin-bottom: 8px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 700;
    }
    .status-bar {
        display: flex;
        gap: 16px;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 16px;
        font-size: 0.78rem;
        color: var(--muted);
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--ok);
        display: inline-block;
        margin-right: 6px;
    }
    .dot.error { background: var(--err); }
    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
    }
    .card {
        background: linear-gradient(180deg, #1b2230 0%, var(--panel) 60%);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.15);
    }
    .card .value { font-size: 1.8rem; font-weight: 800; color: #f0f6fc; }
    .card .label { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
    .services { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
    .svc-tag {
        background: #1f2937;
        border: 1px solid var(--border);
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        color: var(--accent);
    }
    .toolbar {
        display: grid;
        grid-template-columns: 1fr repeat(3, minmax(130px, 180px));
        gap: 10px;
        margin-bottom: 10px;
    }
    .toolbar input,
    .toolbar select,
    .toolbar button {
        width: 100%;
        background: var(--panel);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 8px 10px;
        font-size: 0.8rem;
    }
    .toolbar button {
        cursor: pointer;
        transition: transform 0.15s ease;
    }
    .toolbar button:hover { transform: translateY(-1px); }
    table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
    th {
        text-align: left;
        padding: 8px 10px;
        background: var(--panel);
        border-bottom: 2px solid var(--border);
        color: var(--muted);
        font-weight: 700;
        position: sticky;
        top: 0;
    }
    td { padding: 7px 10px; border-bottom: 1px solid #21262d; }
    tr:hover td { background: #161b22; }
    .level { font-weight: 700; }
    .level-ERROR { color: var(--err); }
    .level-WARN { color: var(--warn); }
    .level-INFO { color: var(--ok); }
    .level-DEBUG { color: var(--muted); }
    .helper {
        font-size: 0.75rem;
        color: var(--muted);
        margin-bottom: 10px;
    }
    @media (max-width: 900px) {
        .toolbar { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 560px) {
        .toolbar { grid-template-columns: 1fr; }
        body { padding: 12px; }
    }
</style>
</head>
<body>
<div class="container">
<h1>Log Ingestion Dashboard</h1>
<div class="status-bar">
    <span><span class="dot" id="conn-dot"></span><span id="conn-text">Connected</span></span>
  <span id="uptime">Uptime: --</span>
  <span id="queue-size">Queue: --</span>
    <span id="last-updated">Updated: --</span>
</div>

<div class="grid">
  <div class="card"><div class="value" id="total">--</div><div class="label">Total Logs Ingested</div></div>
  <div class="card"><div class="value" id="rate">--</div><div class="label">Logs / Second</div></div>
  <div class="card"><div class="value" id="svc-count">--</div><div class="label">Active Services</div></div>
  <div class="card"><div class="value" id="errors">--</div><div class="label">Ingestion Errors</div></div>
</div>

<h2>Services</h2>
<div class="services" id="services"></div>

<h2>Recent Logs</h2>
<div class="toolbar">
    <input id="search" type="text" placeholder="Search message, event, or service" aria-label="Search logs" />
    <select id="level-filter" aria-label="Filter by level">
        <option value="ALL">Level: All</option>
        <option value="ERROR">ERROR</option>
        <option value="WARN">WARN</option>
        <option value="INFO">INFO</option>
        <option value="DEBUG">DEBUG</option>
    </select>
    <select id="service-filter" aria-label="Filter by service">
        <option value="ALL">Service: All</option>
    </select>
    <button id="pause-btn" type="button">Pause Auto Refresh</button>
</div>
<div class="helper" id="shown-count">Showing 0 logs</div>
<div class="card" style="overflow-x:auto;">
<table>
  <thead><tr><th>Timestamp</th><th>Service</th><th>Level</th><th>Event</th><th>Message</th></tr></thead>
  <tbody id="logs-body"></tbody>
</table>
</div>
</div>

<script>
function fmt(n) { return n != null ? n.toLocaleString() : '--'; }
function fmtTime(s) {
  if (!s) return '--';
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60);
  return h > 0 ? h+'h '+m+'m' : m+'m '+Math.floor(s%60)+'s';
}

function esc(v) {
    return String(v == null ? '' : v)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

let latestLogs = [];
let refreshTimer = null;
let paused = false;

function applyFiltersAndRender() {
    const search = document.getElementById('search').value.trim().toLowerCase();
    const levelFilter = document.getElementById('level-filter').value;
    const serviceFilter = document.getElementById('service-filter').value;
    const tbody = document.getElementById('logs-body');

    const filtered = latestLogs.filter((l) => {
        const service = (l.service_name || l.service || '--').toString();
        const level = (l.log_level || l.level || '--').toString().toUpperCase();
        const event = (l.event_type || l.event || '--').toString();
        const msg = (l.message || '').toString();
        const hay = (service + ' ' + level + ' ' + event + ' ' + msg).toLowerCase();

        const levelMatch = levelFilter === 'ALL' || level === levelFilter;
        const serviceMatch = serviceFilter === 'ALL' || service === serviceFilter;
        const searchMatch = !search || hay.indexOf(search) >= 0;
        return levelMatch && serviceMatch && searchMatch;
    });

    document.getElementById('shown-count').textContent = 'Showing ' + filtered.length + ' logs';
    tbody.innerHTML = filtered.map((l) => {
        const service = esc(l.service_name || l.service || '--');
        const level = esc((l.log_level || l.level || '--').toUpperCase());
        const event = esc(l.event_type || l.event || '--');
        const msg = esc((l.message || '').substring(0, 140));
        const ts = esc(l.timestamp || '--');
        return (
            '<tr>' +
                '<td>' + ts + '</td>' +
                '<td>' + service + '</td>' +
                '<td class="level level-' + level + '">' + level + '</td>' +
                '<td>' + event + '</td>' +
                '<td>' + msg + '</td>' +
            '</tr>'
        );
    }).join('');
}

function syncServiceFilter(services) {
    const select = document.getElementById('service-filter');
    const current = select.value;
    const known = new Set(['ALL']);

    const serviceOptions = ['<option value="ALL">Service: All</option>'];
    (services || []).forEach((s) => {
        known.add(s);
        serviceOptions.push('<option value="' + esc(s) + '">' + esc(s) + '</option>');
    });
    select.innerHTML = serviceOptions.join('');

    if (known.has(current)) {
        select.value = current;
    }
}

function setConnectionState(ok) {
    const dot = document.getElementById('conn-dot');
    const text = document.getElementById('conn-text');
    if (ok) {
        dot.classList.remove('error');
        text.textContent = 'Connected';
    } else {
        dot.classList.add('error');
        text.textContent = 'Disconnected';
    }
}

async function poll() {
  try {
    const [statsRes, logsRes] = await Promise.all([
      fetch('/ingestion/stats'), fetch('/ingestion/recent-logs?limit=20')
    ]);
    const stats = await statsRes.json();
    const logsData = await logsRes.json();

    document.getElementById('total').textContent = fmt(stats.total_logs);
    document.getElementById('rate').textContent = stats.logs_per_second;
    document.getElementById('svc-count').textContent = stats.services ? stats.services.length : 0;
    document.getElementById('errors').textContent = fmt(stats.error_count);
    document.getElementById('uptime').textContent = 'Uptime: ' + fmtTime(stats.uptime_seconds);
    document.getElementById('queue-size').textContent = 'Queue: ' + fmt(stats.queue_size);
        document.getElementById('last-updated').textContent = 'Updated: ' + new Date().toLocaleTimeString();

    const svcs = document.getElementById('services');
        svcs.innerHTML = (stats.services || []).map((s) => '<span class="svc-tag">' + esc(s) + '</span>').join('');
        syncServiceFilter(stats.services || []);

        latestLogs = (logsData.logs || []).slice().reverse();
        applyFiltersAndRender();
        setConnectionState(true);
    } catch(e) {
        setConnectionState(false);
        console.error('Poll failed:', e);
    }
}

function togglePause() {
    paused = !paused;
    const btn = document.getElementById('pause-btn');
    if (paused) {
        clearInterval(refreshTimer);
        btn.textContent = 'Resume Auto Refresh';
    } else {
        btn.textContent = 'Pause Auto Refresh';
        refreshTimer = setInterval(poll, 2500);
        poll();
    }
}

document.getElementById('search').addEventListener('input', applyFiltersAndRender);
document.getElementById('level-filter').addEventListener('change', applyFiltersAndRender);
document.getElementById('service-filter').addEventListener('change', applyFiltersAndRender);
document.getElementById('pause-btn').addEventListener('click', togglePause);

poll();
refreshTimer = setInterval(poll, 2500);
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
