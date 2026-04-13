import logging
from collections import defaultdict
from threading import RLock

from config import MONGO_DB, MONGO_URI, USE_MONGO

logger = logging.getLogger("detection.database")

_client = None
_db = None


def get_db():
    global _client, _db

    if not USE_MONGO:
        return None

    if _db is not None:
        return _db

    try:
        from pymongo import MongoClient

        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[MONGO_DB]

        _db.detection_results.create_index("log_id")
        _db.detection_results.create_index("severity")
        _db.detection_results.create_index("timestamp")
        _db.feedback.create_index("log_id")

        logger.info("Connected to MongoDB at %s, database=%s", MONGO_URI, MONGO_DB)
        return _db
    except Exception:
        logger.exception("Failed to connect to MongoDB, falling back to in-memory store")
        return None


class InMemoryDB:
    """Thread-safe in-memory store that mimics basic MongoDB collection APIs."""

    def __init__(self):
        self._lock = RLock()
        self._collections: dict[str, list[dict]] = defaultdict(list)

    def collection(self, name: str) -> "InMemoryCollection":
        return InMemoryCollection(self, name)


class InMemoryCollection:
    def __init__(self, db: InMemoryDB, name: str):
        self._db = db
        self._name = name

    def insert_one(self, doc: dict):
        with self._db._lock:
            self._db._collections[self._name].append(dict(doc))

    def find(self, query: dict | None = None) -> list[dict]:
        query = query or {}
        with self._db._lock:
            return [dict(doc) for doc in self._db._collections[self._name] if self._matches(doc, query)]

    @staticmethod
    def _matches(doc: dict, query: dict) -> bool:
        for key, value in query.items():
            if isinstance(value, dict):
                dv = doc.get(key)
                for op, operand in value.items():
                    if op == "$gte" and (dv is None or dv < operand):
                        return False
                    if op == "$lte" and (dv is None or dv > operand):
                        return False
                    if op == "$in" and dv not in operand:
                        return False
            elif doc.get(key) != value:
                return False
        return True


_memory_db: InMemoryDB | None = None


def get_store():
    global _memory_db

    db = get_db()
    if db is not None:
        return db, True

    if _memory_db is None:
        _memory_db = InMemoryDB()
        logger.info("Using in-memory detection store (MongoDB unavailable or disabled)")

    return _memory_db, False
