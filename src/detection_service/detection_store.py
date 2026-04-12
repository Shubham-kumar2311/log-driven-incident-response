import logging
import json
from datetime import datetime, timezone
from pathlib import Path

from database.mongo_client import get_store
from config import DETECTION_STORE_FILE

logger = logging.getLogger("detection.store")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class DetectionStore:
    def __init__(self):
        self._store, self._is_mongo = get_store()
        self._store_file = Path(DETECTION_STORE_FILE)
        if not self._is_mongo and not getattr(self._store, "_persisted_loaded", False):
            self._load_persisted_records()
            self._store._persisted_loaded = True

    def _col(self, name: str):
        if self._is_mongo:
            return self._store[name]
        return self._store.collection(name)

    def _persist_record(self, collection: str, doc: dict) -> None:
        if self._is_mongo:
            return
        try:
            self._store_file.parent.mkdir(parents=True, exist_ok=True)
            with self._store_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"collection": collection, "doc": doc}, ensure_ascii=True) + "\n")
        except Exception:
            logger.exception("Failed to persist detection record", extra={"collection": collection})

    def _load_persisted_records(self) -> None:
        if not self._store_file.exists():
            return

        loaded = 0
        try:
            with self._store_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    collection = record.get("collection")
                    doc = record.get("doc")
                    if not collection or not isinstance(doc, dict):
                        continue
                    self._col(collection).insert_one(doc)
                    loaded += 1
            if loaded:
                logger.info("Loaded persisted detection records", extra={"loaded_count": loaded})
        except Exception:
            logger.exception("Failed to load persisted detection records")

    def save_detection_result(self, result: dict) -> None:
        doc = dict(result)
        doc.setdefault("timestamp", _now_iso())
        self._col("detection_results").insert_one(doc)
        self._persist_record("detection_results", doc)

    def save_feedback(self, log_id: str, is_false_positive: bool, notes: str = "") -> dict:
        feedback = {
            "log_id": log_id,
            "is_false_positive": bool(is_false_positive),
            "notes": notes,
            "timestamp": _now_iso(),
        }
        self._col("feedback").insert_one(feedback)
        self._persist_record("feedback", feedback)
        logger.info("Feedback captured", extra={"log_id": log_id, "is_false_positive": is_false_positive})
        return feedback

    def get_labeled_anomaly_samples(self) -> list[dict]:
        rows = self._col("detection_results").find({})
        feedback_rows = self._col("feedback").find({})
        feedback_by_log_id = {}
        for fb in feedback_rows:
            log_id = fb.get("log_id")
            if log_id:
                feedback_by_log_id[log_id] = bool(fb.get("is_false_positive", False))

        samples: list[dict] = []
        for row in rows:
            is_positive = bool(
                row.get("rule_triggered")
                or row.get("zscore_triggered")
                or row.get("ml_triggered")
                or row.get("severity") in {"MEDIUM", "HIGH", "CRITICAL"}
            )
            if not is_positive:
                continue

            log_id = row.get("log_id")
            is_false_positive = bool(feedback_by_log_id.get(log_id, False))

            source = "rule"
            if row.get("zscore_triggered") and not row.get("rule_triggered"):
                source = "zscore"
            if row.get("ml_triggered") and not row.get("rule_triggered") and not row.get("zscore_triggered"):
                source = "ml"

            samples.append(
                {
                    "log_id": log_id,
                    "features": row.get("features", {}),
                    "label": 0 if is_false_positive else 1,
                    "source": source,
                    "timestamp": row.get("timestamp"),
                }
            )
        return samples
