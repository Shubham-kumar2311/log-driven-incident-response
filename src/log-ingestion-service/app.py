from fastapi import FastAPI
from ingestion_service import LogIngestionService

app = FastAPI(title="Log Ingestion Service")
service = LogIngestionService()

@app.post("/ingest")
def ingest_log(raw_log: str):
    return service.ingest(raw_log)