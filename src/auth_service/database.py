"""
MongoDB Database Connection
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from config import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB connection manager"""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            cls.db = cls.client[settings.MONGODB_DB]

            # Verify connection
            await cls.client.admin.command("ping")
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB}")

            # Create indexes
            await cls._create_indexes()

        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def _create_indexes(cls):
        """Create database indexes"""
        # Users indexes
        await cls.db.users.create_index("username", unique=True)
        await cls.db.users.create_index("email", unique=True)
        await cls.db.users.create_index("role")
        await cls.db.users.create_index("oauth_key", unique=True, sparse=True)

        # Login logs indexes
        await cls.db.login_logs.create_index("user_id")
        await cls.db.login_logs.create_index([("timestamp", -1)])
        await cls.db.login_logs.create_index("ip_address")
        await cls.db.login_logs.create_index([("ip_address", 1), ("status", 1), ("timestamp", -1)])

        logger.info("Database indexes created")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if cls.db is None:
            raise RuntimeError("Database not connected")
        return cls.db


def get_database() -> AsyncIOMotorDatabase:
    """Dependency for getting database"""
    return Database.get_db()
