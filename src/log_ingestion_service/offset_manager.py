import json
import os
from config import OFFSET_FILE


class OffsetManager:
    def __init__(self):
        if os.path.exists(OFFSET_FILE):
            with open(OFFSET_FILE, "r") as f:
                self.offsets = json.load(f)
        else:
            self.offsets = {}

    def get_offset(self, filename: str) -> int:
        return self.offsets.get(filename, 0)

    def update_offset(self, filename: str, offset: int):
        self.offsets[filename] = offset
        with open(OFFSET_FILE, "w") as f:
            json.dump(self.offsets, f)