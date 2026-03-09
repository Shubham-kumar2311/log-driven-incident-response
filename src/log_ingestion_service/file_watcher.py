import os
import json
import time
from datetime import datetime

from config import LOG_DIR, POLL_INTERVAL
from offset_manager import OffsetManager
from publisher import publish_event


class FileWatcher:

    def __init__(self):
        self.offset_manager = OffsetManager()

    def _process_file(self, filename: str):

        file_path = os.path.join(LOG_DIR, filename)

        if not os.path.isfile(file_path):
            return

        last_offset = self.offset_manager.get_offset(filename)

        try:
            with open(file_path, "r") as f:

                f.seek(last_offset)

                lines = f.readlines()

                new_offset = f.tell()

        except Exception as e:
            print(f"[INGESTION ERROR] Failed reading {filename}: {e}")
            return

        for line in lines:

            try:

                event = json.loads(line.strip())

                enriched_event = self._enrich_event(event, filename)

                publish_event(enriched_event)

            except json.JSONDecodeError:
                # could send to dead-letter queue later
                continue

        self.offset_manager.update_offset(filename, new_offset)

    def _enrich_event(self, event: dict, filename: str) -> dict:

        event["ingested_at"] = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        event["ingestion_source_file"] = filename

        return event

    def watch(self):

        while True:

            try:

                for filename in os.listdir(LOG_DIR):

                    if not filename.endswith(".log"):
                        continue

                    self._process_file(filename)

            except Exception as e:

                print(f"[INGESTION ERROR] {e}")

            time.sleep(POLL_INTERVAL)