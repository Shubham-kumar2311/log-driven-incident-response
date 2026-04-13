import sys
import os
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.app import app
from config import HOST, PORT

# Export app for uvicorn
# Usage: python -m uvicorn app:app --port 8005 --reload


if __name__ == "__main__":
	uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
