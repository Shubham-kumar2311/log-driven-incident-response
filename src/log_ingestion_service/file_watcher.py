import os
import json
import time
import logging

from config import LOG_DIR, POLL_INTERVAL
from offset_manager import OffsetManager
from processor import process_log
from event_queue import enqueue
from stats_tracker import stats

logger = logging.getLogger("ingestion.file_watcher")


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
        except OSError as e:
            logger.error("Failed reading %s: %s", filename, e)
            return

        processed = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                raw["ingestion_source_file"] = filename
                normalized = process_log(raw)
                if normalized:
                    enqueue(normalized)
                    processed += 1
            except json.JSONDecodeError:
                stats.record_error()
                logger.debug("Skipping malformed JSON in %s", filename)

        if processed > 0:
            logger.info("Queued %d logs from %s", processed, filename)

        self.offset_manager.update_offset(filename, new_offset)

    def watch(self):
        logger.info("File watcher started, watching %s", LOG_DIR)
        while True:
            try:
                for filename in os.listdir(LOG_DIR):
                    if not filename.endswith(".log"):
                        continue
                    self._process_file(filename)
            except Exception as e:
                logger.error("Watch loop error: %s", e)
                stats.record_error()
            time.sleep(POLL_INTERVAL)
