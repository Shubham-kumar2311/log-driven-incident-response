import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from db.mongo_client import get_database
from config import PLAYBOOKS_COLLECTION

logger = logging.getLogger(__name__)


class PlaybookRepository:
    """Repository layer for playbook CRUD operations."""

    def __init__(self):
        self._collection: Optional[Collection] = None

    @property
    def collection(self) -> Collection:
        """Lazy-load the collection."""
        if self._collection is None:
            db = get_database()
            self._collection = db[PLAYBOOKS_COLLECTION]
            self._ensure_indexes()
        return self._collection

    def _ensure_indexes(self):
        """Create indexes for efficient queries."""
        try:
            self.collection.create_index("signal_type", unique=True)
            self.collection.create_index("enabled")
            logger.info("Playbook indexes ensured")
        except PyMongoError as e:
            logger.warning(f"Could not create indexes: {e}")

    def _serialize_playbook(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to API-friendly format."""
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        # Convert datetime to ISO string if present
        for field in ["created_at", "updated_at"]:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = doc[field].isoformat()
        return doc

    def get_playbook(self, signal_type: str) -> Optional[Dict[str, Any]]:
        """Get a playbook by signal type."""
        try:
            doc = self.collection.find_one({"signal_type": signal_type})
            return self._serialize_playbook(doc)
        except PyMongoError as e:
            logger.error(f"Error fetching playbook for {signal_type}: {e}")
            return None

    def get_playbook_by_id(self, playbook_id: str) -> Optional[Dict[str, Any]]:
        """Get a playbook by its ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(playbook_id)})
            return self._serialize_playbook(doc)
        except Exception as e:
            logger.error(f"Error fetching playbook {playbook_id}: {e}")
            return None

    def get_all_playbooks(self) -> List[Dict[str, Any]]:
        """Get all playbooks."""
        try:
            docs = list(self.collection.find().sort("signal_type", 1))
            return [self._serialize_playbook(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error fetching all playbooks: {e}")
            return []

    def get_enabled_playbook(self, signal_type: str) -> Optional[Dict[str, Any]]:
        """Get an enabled playbook by signal type."""
        try:
            doc = self.collection.find_one({
                "signal_type": signal_type,
                "enabled": True
            })
            return self._serialize_playbook(doc)
        except PyMongoError as e:
            logger.error(f"Error fetching enabled playbook for {signal_type}: {e}")
            return None

    def create_playbook(self, playbook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new playbook."""
        try:
            now = datetime.now(timezone.utc)
            doc = {
                "signal_type": playbook_data["signal_type"],
                "action": playbook_data["action"],
                "description": playbook_data.get("description", ""),
                "enabled": playbook_data.get("enabled", True),
                "priority": playbook_data.get("priority", 1),
                "parameters": playbook_data.get("parameters", {}),
                "created_at": now,
                "updated_at": now
            }
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            logger.info(f"Created playbook: {playbook_data['signal_type']}")
            return self._serialize_playbook(doc)
        except PyMongoError as e:
            logger.error(f"Error creating playbook: {e}")
            return None

    def update_playbook(self, playbook_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing playbook."""
        try:
            # Remove id if present in update data
            update_data.pop("id", None)
            update_data.pop("_id", None)
            update_data["updated_at"] = datetime.now(timezone.utc)

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(playbook_id)},
                {"$set": update_data},
                return_document=True
            )
            if result:
                logger.info(f"Updated playbook: {playbook_id}")
                return self._serialize_playbook(result)
            return None
        except Exception as e:
            logger.error(f"Error updating playbook {playbook_id}: {e}")
            return None

    def toggle_playbook(self, playbook_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        """Enable or disable a playbook."""
        return self.update_playbook(playbook_id, {"enabled": enabled})

    def delete_playbook(self, playbook_id: str) -> bool:
        """Delete a playbook."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(playbook_id)})
            if result.deleted_count > 0:
                logger.info(f"Deleted playbook: {playbook_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting playbook {playbook_id}: {e}")
            return False

    def seed_default_playbooks(self):
        """Seed default playbooks if collection is empty."""
        if self.collection.count_documents({}) > 0:
            logger.info("Playbooks already exist, skipping seed")
            return

        default_playbooks = [
            {
                "signal_type": "DB_SLOW_QUERY",
                "action": "restart_database",
                "description": "Restart database service when query latency exceeds threshold",
                "enabled": True,
                "priority": 1,
                "parameters": {"graceful": True, "timeout": 30}
            },
            {
                "signal_type": "HTTP_ERROR_SPIKE",
                "action": "restart_api",
                "description": "Restart API servers when HTTP 5xx error rate spikes",
                "enabled": True,
                "priority": 2,
                "parameters": {"rolling": True, "batch_size": 2}
            },
            {
                "signal_type": "AUTH_FAILURE_SPIKE",
                "action": "lock_accounts",
                "description": "Lock suspicious accounts during brute force attacks",
                "enabled": True,
                "priority": 1,
                "parameters": {"lock_duration_minutes": 30}
            },
            {
                "signal_type": "DEPLOYMENT_FAILURE",
                "action": "rollback_deployment",
                "description": "Automatically rollback failed deployments",
                "enabled": True,
                "priority": 1,
                "parameters": {"keep_logs": True}
            },
            {
                "signal_type": "HIGH_LATENCY",
                "action": "scale_service",
                "description": "Scale up service instances when latency is high",
                "enabled": False,
                "priority": 2,
                "parameters": {"scale_factor": 2, "max_instances": 10}
            },
            {
                "signal_type": "CACHE_ERROR",
                "action": "restart_cache",
                "description": "Restart cache service on connection errors",
                "enabled": True,
                "priority": 1,
                "parameters": {"flush_on_restart": False}
            }
        ]

        for playbook in default_playbooks:
            self.create_playbook(playbook)

        logger.info(f"Seeded {len(default_playbooks)} default playbooks")
