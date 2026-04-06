import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from config import MONGO_URI, MONGO_DB

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Singleton MongoDB client for the response service."""

    _instance: Optional["MongoDBClient"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Database:
        """Establish connection to MongoDB."""
        if self._db is not None:
            return self._db

        try:
            self._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.admin.command("ping")
            self._db = self._client[MONGO_DB]
            logger.info(f"Connected to MongoDB: {MONGO_URI}/{MONGO_DB}")
            return self._db
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_db(self) -> Database:
        """Get database instance, connecting if necessary."""
        if self._db is None:
            return self.connect()
        return self._db

    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False


# Global instance
mongo_client = MongoDBClient()


def get_database() -> Database:
    """Get the MongoDB database instance."""
    return mongo_client.get_db()
