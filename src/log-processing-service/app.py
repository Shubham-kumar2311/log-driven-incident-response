from fastapi import FastAPI
from processing_service import LogProcessingService

app = FastAPI(title="Log Processing Service")
service = LogProcessingService()

@app.post("/process")
def process_log(payload: dict):
    return service.process(payload["raw_log"])
