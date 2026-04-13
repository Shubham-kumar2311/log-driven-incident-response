from pathlib import Path
from contextlib import asynccontextmanager

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

FEATURE_ORDER = [
    "request_rate",
    "error_ratio",
    "failed_login_count",
    "unique_ip_count",
    "endpoint_entropy",
    "time_of_day",
    "z_score_request_rate",
    "z_score_error_ratio",
]

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"


class PredictPayload(BaseModel):
    request_rate: float
    error_ratio: float
    failed_login_count: int
    unique_ip_count: int
    endpoint_entropy: float
    time_of_day: int
    z_score_request_rate: float
    z_score_error_ratio: float


model = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global model
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    yield


app = FastAPI(title="Isolation Forest ML Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy" if model is not None else "not_ready",
        "model_path": str(MODEL_PATH),
    }


@app.post("/predict")
def predict(payload: PredictPayload) -> dict:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    vector = np.array([[float(getattr(payload, name)) for name in FEATURE_ORDER]], dtype=float)

    # Per requirement: anomaly if decision_function score < 0
    score = float(model.decision_function(vector)[0])
    return {
        "anomaly_score": score,
        "is_anomaly": score < 0.0,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
