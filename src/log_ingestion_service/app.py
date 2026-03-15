import sys
import queue
import logging
import threading

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse

from config import MAX_BATCH_SIZE
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
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f1117; color: #e1e4e8; padding: 20px; }
  h1 { font-size: 1.4rem; margin-bottom: 16px; color: #58a6ff; }
  h2 { font-size: 1rem; margin-bottom: 8px; color: #8b949e; text-transform: uppercase;
       letter-spacing: 0.5px; font-weight: 600; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 12px; margin-bottom: 20px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
          padding: 16px; }
  .card .value { font-size: 1.8rem; font-weight: 700; color: #f0f6fc; }
  .card .label { font-size: 0.75rem; color: #8b949e; margin-top: 4px; }
  .services { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
  .svc-tag { background: #1f2937; border: 1px solid #30363d; padding: 4px 10px;
             border-radius: 12px; font-size: 0.75rem; color: #58a6ff; }
  table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  th { text-align: left; padding: 8px 10px; background: #161b22;
       border-bottom: 2px solid #30363d; color: #8b949e; font-weight: 600; }
  td { padding: 6px 10px; border-bottom: 1px solid #21262d; }
  tr:hover td { background: #161b22; }
  .level-ERROR, .level-WARN { color: #f85149; }
  .level-INFO { color: #3fb950; }
  .level-DEBUG { color: #8b949e; }
  .status-bar { display: flex; gap: 16px; align-items: center; margin-bottom: 16px;
                font-size: 0.75rem; color: #8b949e; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #3fb950;
         display: inline-block; margin-right: 4px; }
</style>
</head>
<body>
<h1>Log Ingestion Dashboard</h1>
<div class="status-bar">
  <span><span class="dot"></span> Connected</span>
  <span id="uptime">Uptime: --</span>
  <span id="queue-size">Queue: --</span>
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
<div class="card" style="overflow-x:auto;">
<table>
  <thead><tr><th>Timestamp</th><th>Service</th><th>Level</th><th>Event</th><th>Message</th></tr></thead>
  <tbody id="logs-body"></tbody>
</table>
</div>

<script>
function fmt(n) { return n != null ? n.toLocaleString() : '--'; }
function fmtTime(s) {
  if (!s) return '--';
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60);
  return h > 0 ? h+'h '+m+'m' : m+'m '+Math.floor(s%60)+'s';
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

    const svcs = document.getElementById('services');
    svcs.innerHTML = (stats.services||[]).map(s => '<span class="svc-tag">'+s+'</span>').join('');

    const tbody = document.getElementById('logs-body');
    const logs = (logsData.logs||[]).reverse();
    tbody.innerHTML = logs.map(l =>
      '<tr>' +
        '<td>'+(l.timestamp||'--')+'</td>' +
        '<td>'+(l.service_name||l.service||'--')+'</td>' +
        '<td class="level-'+(l.log_level||l.level||'')+'">'+(l.log_level||l.level||'--')+'</td>' +
        '<td>'+(l.event_type||l.event||'--')+'</td>' +
        '<td>'+(l.message||'').substring(0,80)+'</td>' +
      '</tr>'
    ).join('');
  } catch(e) { console.error('Poll failed:', e); }
}

poll();
setInterval(poll, 2500);
</script>
</body>
</html>"""
