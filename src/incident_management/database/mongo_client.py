import logging
from collections import defaultdict
from threading import RLock

from config import MONGO_DB, MONGO_URI, USE_MONGO

logger = logging.getLogger("incident.database")

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

        _db.incidents.create_index("incident_id", unique=True)
        _db.incidents.create_index("status")
        _db.incidents.create_index("severity")
        _db.incidents.create_index("affected_service")
        _db.incidents.create_index("correlation_key")
        _db.incidents.create_index("created_at")
        _db.incident_timeline.create_index("incident_id")
        _db.incident_timeline.create_index("timestamp")
        _db.analyst_actions.create_index("incident_id")
        _db.incident_notes.create_index("incident_id")

        logger.info("Connected to MongoDB at %s, database=%s", MONGO_URI, MONGO_DB)
        return _db
    except Exception:
        logger.exception("Failed to connect to MongoDB, falling back to in-memory store")
        return None


class InMemoryDB:
    """Thread-safe in-memory store that mirrors MongoDB collection semantics."""

    def __init__(self):
        self._lock = RLock()
        self._collections: dict[str, list[dict]] = defaultdict(list)
        self._indexes: dict[str, dict[str, dict]] = defaultdict(dict)

    def collection(self, name: str) -> "InMemoryCollection":
        return InMemoryCollection(self, name)


class InMemoryCollection:

    def __init__(self, db: InMemoryDB, name: str):
        self._db = db
        self._name = name

    def insert_one(self, doc: dict):
        with self._db._lock:
            self._db._collections[self._name].append(dict(doc))

    def find_one(self, query: dict) -> dict | None:
        with self._db._lock:
            for doc in self._db._collections[self._name]:
                if self._matches(doc, query):
                    return dict(doc)
        return None

    def find(self, query: dict | None = None) -> list[dict]:
        query = query or {}
        with self._db._lock:
            results = []
            for doc in self._db._collections[self._name]:
                if self._matches(doc, query):
                    results.append(dict(doc))
            return results

    def update_one(self, query: dict, update: dict) -> bool:
        with self._db._lock:
            for doc in self._db._collections[self._name]:
                if self._matches(doc, query):
                    if "$set" in update:
                        doc.update(update["$set"])
                    if "$push" in update:
                        for k, v in update["$push"].items():
                            if k not in doc:
                                doc[k] = []
                            doc[k].append(v)
                    if "$addToSet" in update:
                        for k, v in update["$addToSet"].items():
                            if k not in doc:
                                doc[k] = []
                            if v not in doc[k]:
                                doc[k].append(v)
                    if "$inc" in update:
                        for k, v in update["$inc"].items():
                            doc[k] = doc.get(k, 0) + v
                    return True
        return False

    def count_documents(self, query: dict | None = None) -> int:
        return len(self.find(query or {}))

    @staticmethod
    def _matches(doc: dict, query: dict) -> bool:
        for key, value in query.items():
            if key == "$or":
                if not any(InMemoryCollection._matches(doc, clause) for clause in value):
                    return False
                continue
            if isinstance(value, dict):
                dv = doc.get(key)
                for op, operand in value.items():
                    if op == "$in" and dv not in operand:
                        return False
                    if op == "$gte" and (dv is None or dv < operand):
                        return False
                    if op == "$lte" and (dv is None or dv > operand):
                        return False
                    if op == "$ne" and dv == operand:
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
        logger.info("Using in-memory store (MongoDB unavailable or disabled)")

    return _memory_db, False
