import requests
from logger import write_log

PROCESSING_URL = "http://localhost:8001/process"

class LogIngestionService:

    def ingest(self, raw_log: str):
        write_log("logs/input_log.txt", raw_log)

        response = requests.post(
            PROCESSING_URL,
            json={"raw_log": raw_log}
        )

        write_log("logs/output_log.txt", response.text)
        return response.json()