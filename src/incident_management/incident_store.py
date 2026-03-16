import logging

from database.mongo_client import get_store
from models.incident_model import timeline_entry, analyst_note

logger = logging.getLogger("incident.store")


class IncidentStore:

    def __init__(self):
        store, self._is_mongo = get_store()
        self._store = store

    def _col(self, name: str):
        if self._is_mongo:
            return self._store[name]
        return self._store.collection(name)

    @staticmethod
    def _clean(doc: dict | None) -> dict | None:
        """Strip MongoDB's _id so documents are JSON-serializable."""
        if doc and "_id" in doc:
            d = dict(doc)
            d.pop("_id")
            return d
        return doc

    # ── Incidents ────────────────────────────────────────────────────

    def save_incident(self, incident: dict) -> None:
        self._col("incidents").insert_one(dict(incident))  # copy avoids _id mutation
        self._add_timeline(
            incident["incident_id"],
            "incident_created",
            f"Incident created: {incident['description']}",
        )
        logger.info("Incident saved", extra={"incident_id": incident["incident_id"]})

    def get_incident(self, incident_id: str) -> dict | None:
        return self._clean(self._col("incidents").find_one({"incident_id": incident_id}))

    def find_open_by_correlation_key(self, key: str, cutoff: str) -> dict | None:
        results = list(self._col("incidents").find({
            "correlation_key": key,
            "status": {"$in": ["open", "investigating"]},
            "created_at": {"$gte": cutoff},
        }))
        return self._clean(results[0]) if results else None

    def update_incident(self, incident_id: str, updates: dict) -> dict | None:
        self._col("incidents").update_one(
            {"incident_id": incident_id},
            {"$set": updates},
        )
        return self.get_incident(incident_id)

    def add_signal_to_incident(self, incident_id: str, signal: dict) -> dict | None:
        self._col("incidents").update_one(
            {"incident_id": incident_id},
            {
                "$addToSet": {"signal_ids": signal.get("signal_id", "")},
                "$inc": {"signal_count": 1},
                "$set": {
                    "last_signal_at": signal.get("detected_at", ""),
                    "updated_at": signal.get("detected_at", ""),
                    "risk_score": max(
                        self.get_incident(incident_id).get("risk_score", 0),
                        signal.get("risk_score", 0),
                    ),
                },
            },
        )
        self._add_timeline(
            incident_id,
            "signal_correlated",
            f"Signal {signal.get('signal_id', 'unknown')} correlated "
            f"(type={signal.get('signal_type')}, severity={signal.get('severity')})",
            metadata={"signal_id": signal.get("signal_id"), "signal_type": signal.get("signal_type")},
        )
        return self.get_incident(incident_id)

    def list_incidents(self, filters: dict | None = None) -> list[dict]:
        query = {}
        if filters:
            if filters.get("status"):
                query["status"] = filters["status"]
            if filters.get("severity"):
                query["severity"] = filters["severity"]
            if filters.get("affected_service"):
                query["affected_service"] = filters["affected_service"]
            if filters.get("environment"):
                query["environment"] = filters["environment"]
        return [self._clean(d) for d in self._col("incidents").find(query)]

    def list_active_incidents(self) -> list[dict]:
        return [self._clean(d) for d in self._col("incidents").find({
            "status": {"$in": ["open", "investigating", "mitigated"]},
        })]

    def update_status(self, incident_id: str, new_status: str, actor: str = "system") -> dict | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        old_status = incident["status"]
        from models.incident_model import _now
        self._col("incidents").update_one(
            {"incident_id": incident_id},
            {"$set": {"status": new_status, "updated_at": _now()}},
        )
        self._add_timeline(
            incident_id,
            "status_change",
            f"Status changed: {old_status} -> {new_status}",
            actor=actor,
            metadata={"old_status": old_status, "new_status": new_status},
        )
        self._add_action(incident_id, actor, "status_change", f"{old_status} -> {new_status}")
        return self.get_incident(incident_id)

    def assign_analyst(self, incident_id: str, analyst: str) -> dict | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        from models.incident_model import _now
        self._col("incidents").update_one(
            {"incident_id": incident_id},
            {"$set": {"assigned_analyst": analyst, "updated_at": _now()}},
        )
        self._add_timeline(
            incident_id,
            "analyst_assigned",
            f"Incident assigned to {analyst}",
            actor=analyst,
        )
        self._add_action(incident_id, analyst, "assignment", f"Assigned to {analyst}")
        return self.get_incident(incident_id)

    def update_severity(self, incident_id: str, new_severity: str) -> None:
        incident = self.get_incident(incident_id)
        if not incident:
            return
        old = incident.get("severity")
        if old != new_severity:
            from models.incident_model import _now
            self._col("incidents").update_one(
                {"incident_id": incident_id},
                {"$set": {"severity": new_severity, "updated_at": _now()}},
            )
            self._add_timeline(
                incident_id,
                "severity_change",
                f"Severity escalated: {old} -> {new_severity}",
                metadata={"old_severity": old, "new_severity": new_severity},
            )

    def get_incident_count(self) -> int:
        return self._col("incidents").count_documents({})

    # ── Timeline ────────────────────────────────────────────────────

    def _add_timeline(self, incident_id: str, event_type: str, description: str,
                      actor: str = "system", metadata: dict | None = None) -> None:
        entry = timeline_entry(incident_id, event_type, description, actor, metadata)
        self._col("incident_timeline").insert_one(dict(entry))

    def get_timeline(self, incident_id: str) -> list[dict]:
        entries = [self._clean(e) for e in self._col("incident_timeline").find({"incident_id": incident_id})]
        return sorted(entries, key=lambda e: e.get("timestamp", ""))

    # ── Notes ───────────────────────────────────────────────────────

    def add_note(self, incident_id: str, analyst: str, content: str) -> dict:
        note = analyst_note(incident_id, analyst, content)
        self._col("incident_notes").insert_one(dict(note))
        self._add_timeline(
            incident_id,
            "note_added",
            f"Note added by {analyst}",
            actor=analyst,
        )
        return note

    def get_notes(self, incident_id: str) -> list[dict]:
        notes = [self._clean(n) for n in self._col("incident_notes").find({"incident_id": incident_id})]
        return sorted(notes, key=lambda n: n.get("created_at", ""))

    # ── Actions ─────────────────────────────────────────────────────

    def _add_action(self, incident_id: str, analyst: str, action_type: str, details: str) -> None:
        from models.incident_model import _now, _uuid
        self._col("analyst_actions").insert_one({
            "action_id": _uuid(),
            "incident_id": incident_id,
            "analyst": analyst,
            "action_type": action_type,
            "details": details,
            "timestamp": _now(),
        })

    def get_actions(self, incident_id: str) -> list[dict]:
        actions = [self._clean(a) for a in self._col("analyst_actions").find({"incident_id": incident_id})]
        return sorted(actions, key=lambda a: a.get("timestamp", ""))
