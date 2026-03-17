import json
import os
import threading
import logging

from config import OFFSET_FILE

logger = logging.getLogger("ingestion.offsets")


class OffsetManager:
    def __init__(self):
        self._lock = threading.Lock()
        if os.path.exists(OFFSET_FILE):
            try:
                with open(OFFSET_FILE, "r") as f:
                    self.offsets = json.load(f)
            except (json.JSONDecodeError, OSError):
                logger.warning("Corrupt offset file, starting fresh")
                self.offsets = {}
        else:
            self.offsets = {}

    def get_offset(self, filename: str) -> int:
        with self._lock:
            return self.offsets.get(filename, 0)

    def update_offset(self, filename: str, offset: int):
        with self._lock:
            self.offsets[filename] = offset
            try:
                with open(OFFSET_FILE, "w") as f:
                    json.dump(self.offsets, f)
            except OSError as e:
                logger.error("Failed saving offsets: %s", e)
