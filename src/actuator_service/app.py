"""
Actuator Service - Main Entry Point

Start the service with:
    python app.py

Or with uvicorn directly:
    uvicorn api.app:app --port 8006 --reload
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8006,
        reload=True
    )
