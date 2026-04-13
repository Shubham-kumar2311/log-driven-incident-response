import os
from pathlib import Path

import joblib
import numpy as np
import requests
from dotenv import load_dotenv
from sklearn.ensemble import IsolationForest

SERVICE_DIR = Path(__file__).resolve().parent
load_dotenv(SERVICE_DIR / ".env")

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


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _row_from_doc(doc: dict) -> list[float]:
    features = doc.get("features") or {}
    return [_to_float(features.get(name, 0.0)) for name in FEATURE_ORDER]


def load_training_rows() -> np.ndarray:
    detection_url = os.getenv("DETECTION_SERVICE_URL", "http://localhost:8003/training/labeled-data")
    
    try:
        response = requests.get(detection_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        docs = data.get("samples", [])
    except requests.RequestException as e:
        print(f"Warning: Failed to fetch from detection service ({e}), using synthetic data")
        docs = []
    
    if not docs:
        print("No real training data, generating synthetic samples...")
        # Generate synthetic training data: mix of normal and anomalous patterns
        docs = []
        np.random.seed(42)
        for i in range(1000):
            # Normal patterns
            if i < 800:
                features = {
                    "request_rate": np.random.uniform(1, 10),
                    "error_ratio": np.random.uniform(0, 0.1),
                    "failed_login_count": np.random.randint(0, 2),
                    "unique_ip_count": np.random.randint(1, 5),
                    "endpoint_entropy": np.random.uniform(2, 4),
                    "time_of_day": np.random.randint(0, 24),
                    "z_score_request_rate": np.random.uniform(-1, 1),
                    "z_score_error_ratio": np.random.uniform(-1, 1),
                }
            # Anomalous patterns (weakly labeled as positive for training)
            else:
                features = {
                    "request_rate": np.random.uniform(50, 200),  # High rate
                    "error_ratio": np.random.uniform(0.5, 1.0),  # High errors
                    "failed_login_count": np.random.randint(5, 20),
                    "unique_ip_count": np.random.randint(10, 50),
                    "endpoint_entropy": np.random.uniform(4, 5),
                    "time_of_day": np.random.randint(0, 24),
                    "z_score_request_rate": np.random.uniform(2, 5),
                    "z_score_error_ratio": np.random.uniform(2, 5),
                }
            docs.append({"features": features})
    
    vectors = [_row_from_doc(doc) for doc in docs]
    return np.array(vectors, dtype=float)


def train_and_save_model(out_path: Path) -> Path:
    X = load_training_rows()
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X)
    joblib.dump(model, out_path)
    return out_path


def main() -> None:
    model_path = SERVICE_DIR / "model.pkl"
    path = train_and_save_model(model_path)
    print(f"Isolation Forest model saved to: {path}")


if __name__ == "__main__":
    main()
