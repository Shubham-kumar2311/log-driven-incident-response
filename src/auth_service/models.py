"""
Database Models
User and LoginLog models for MongoDB
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId
from enum import Enum

from database import Database
from utils.password import hash_password
import logging

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles"""
    USER = "USER"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"


class LoginStatus(str, Enum):
    """Login attempt status"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ============================================================
# USER MODEL
# ============================================================

class User:
    """User model operations"""

    collection = "users"

    @classmethod
    def _db(cls):
        return Database.get_db()[cls.collection]

    @classmethod
    async def create(
        cls,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER
    ) -> Dict[str, Any]:
        """Create new user"""
        user_doc = {
            "username": username.lower().strip(),
            "email": email.lower().strip(),
            "password_hash": hash_password(password),
            "role": role.value,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login_at": None,
            "last_login_ip": None
        }

        result = await cls._db().insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        logger.info(f"User created: {username} with role {role.value}")
        return cls._serialize(user_doc)

    @classmethod
    async def find_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        try:
            user = await cls._db().find_one({"_id": ObjectId(user_id)})
            return cls._serialize(user) if user else None
        except Exception:
            return None

    @classmethod
    async def find_by_username(cls, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username (includes password_hash)"""
        user = await cls._db().find_one({"username": username.lower().strip()})
        return cls._serialize(user, include_password=True) if user else None

    @classmethod
    async def find_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email (includes password_hash)"""
        user = await cls._db().find_one({"email": email.lower().strip()})
        return cls._serialize(user, include_password=True) if user else None

    @classmethod
    async def find_by_username_or_email(cls, identifier: str) -> Optional[Dict[str, Any]]:
        """Find user by username or email"""
        identifier = identifier.lower().strip()
        user = await cls._db().find_one({
            "$or": [
                {"username": identifier},
                {"email": identifier}
            ]
        })
        return cls._serialize(user, include_password=True) if user else None

    @classmethod
    async def exists_by_username(cls, username: str) -> bool:
        """Check if username exists"""
        count = await cls._db().count_documents({"username": username.lower().strip()})
        return count > 0

    @classmethod
    async def exists_by_email(cls, email: str) -> bool:
        """Check if email exists"""
        count = await cls._db().count_documents({"email": email.lower().strip()})
        return count > 0

    @classmethod
    async def update_last_login(cls, user_id: str, ip_address: str) -> None:
        """Update last login info"""
        await cls._db().update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "last_login_at": datetime.utcnow(),
                    "last_login_ip": ip_address
                }
            }
        )

    @classmethod
    async def find_all(cls, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get all users with pagination"""
        total = await cls._db().count_documents({})
        skip = (page - 1) * limit

        cursor = cls._db().find({}).skip(skip).limit(limit).sort("created_at", -1)
        users = await cursor.to_list(length=limit)

        return {
            "users": [cls._serialize(u) for u in users],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

    @classmethod
    def _serialize(cls, user: Optional[Dict], include_password: bool = False) -> Optional[Dict[str, Any]]:
        """Serialize user document"""
        if not user:
            return None

        result = {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "last_login_at": user["last_login_at"].isoformat() if user.get("last_login_at") else None,
            "last_login_ip": user.get("last_login_ip")
        }

        if include_password:
            result["password_hash"] = user.get("password_hash")

        return result


# ============================================================
# LOGIN LOG MODEL
# ============================================================

class LoginLog:
    """Login log model operations"""

    collection = "login_logs"

    @classmethod
    def _db(cls):
        return Database.get_db()[cls.collection]

    @classmethod
    async def create(
        cls,
        user_id: Optional[str],
        username_attempted: str,
        ip_address: str,
        status: LoginStatus,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create login log entry"""
        log_doc = {
            "user_id": user_id,
            "username_attempted": username_attempted,
            "ip_address": ip_address,
            "status": status.value,
            "user_agent": user_agent,
            "failure_reason": failure_reason,
            "timestamp": datetime.utcnow()
        }

        result = await cls._db().insert_one(log_doc)
        log_doc["_id"] = result.inserted_id

        logger.info(f"Login attempt logged: {status.value} for {username_attempted} from {ip_address}")
        return cls._serialize(log_doc)

    @classmethod
    async def get_recent_failed_by_ip(cls, ip_address: str, window_seconds: int = 120) -> int:
        """Count recent failed login attempts from IP"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)

        count = await cls._db().count_documents({
            "ip_address": ip_address,
            "status": LoginStatus.FAILED.value,
            "timestamp": {"$gte": cutoff}
        })
        return count

    @classmethod
    async def get_recent_failed_by_username(cls, username: str, window_seconds: int = 120) -> int:
        """Count recent failed login attempts for username"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)

        count = await cls._db().count_documents({
            "username_attempted": username.lower(),
            "status": LoginStatus.FAILED.value,
            "timestamp": {"$gte": cutoff}
        })
        return count

    @classmethod
    async def is_new_ip_for_user(cls, user_id: str, ip_address: str) -> bool:
        """Check if this IP is new for the user"""
        existing = await cls._db().find_one({
            "user_id": user_id,
            "ip_address": ip_address,
            "status": LoginStatus.SUCCESS.value
        })
        return existing is None

    @classmethod
    async def find_all(
        cls,
        page: int = 1,
        limit: int = 50,
        user_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get login logs with filtering"""
        query = {}
        if user_id:
            query["user_id"] = user_id
        if status:
            query["status"] = status

        total = await cls._db().count_documents(query)
        skip = (page - 1) * limit

        cursor = cls._db().find(query).skip(skip).limit(limit).sort("timestamp", -1)
        logs = await cursor.to_list(length=limit)

        return {
            "logs": [cls._serialize(log) for log in logs],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

    @classmethod
    def _serialize(cls, log: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Serialize login log document"""
        if not log:
            return None

        return {
            "id": str(log["_id"]),
            "user_id": log.get("user_id"),
            "username_attempted": log.get("username_attempted"),
            "ip_address": log.get("ip_address"),
            "status": log.get("status"),
            "user_agent": log.get("user_agent"),
            "failure_reason": log.get("failure_reason"),
            "timestamp": log["timestamp"].isoformat() if log.get("timestamp") else None
        }
