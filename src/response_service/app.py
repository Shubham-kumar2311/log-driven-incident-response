from fastapi import FastAPI
from playbook_engine import PlaybookEngine

app = FastAPI(
    title="Response Service",
    version="1.0"
)

engine = PlaybookEngine()


@app.post("/simulate-response")
def simulate_response(incident: dict):

    result = engine.execute(incident)

    return result