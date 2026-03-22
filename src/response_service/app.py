import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.app import app

# Export app for uvicorn
# Usage: python -m uvicorn app:app --port 8002 --reload
