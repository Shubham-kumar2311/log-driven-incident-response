"""
Actuator Service - Main Entry Point

Start the service with:
    python app.py

Or with uvicorn directly:
    uvicorn api.app:app --port 8007 --reload
"""
import uvicorn
from config import HOST, PORT, RELOAD

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=HOST,
        port=PORT,
        reload=RELOAD
    )
