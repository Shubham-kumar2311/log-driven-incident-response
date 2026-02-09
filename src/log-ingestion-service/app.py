from fastapi import FastAPI, Request
from ingestion_service import LogIngestionService

app = FastAPI(title="Log Ingestion Service")
service = LogIngestionService()

@app.post("/ingest")
async def ingest_log(request: Request):
    raw_log = (await request.body()).decode("utf-8")
    return service.ingest(raw_log)
