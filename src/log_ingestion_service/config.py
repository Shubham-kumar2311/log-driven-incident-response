import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
OFFSET_FILE = os.getenv("OFFSET_FILE", "offsets.json")

POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", 1.0))