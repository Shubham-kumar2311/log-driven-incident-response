import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from repository.playbook_repository import PlaybookRepository
from actions.executor import ActionExecutor, ActionResult, ActionStatus

logger = logging.getLogger(__name__)


class PlaybookEngine:
    """Engine for matching incidents to playbooks and executing actions."""

    def __init__(self, repository: Optional[PlaybookRepository] = None):
        self.repository = repository or PlaybookRepository()
        self.executor = ActionExecutor()

    def _extract_signal_type(self, incident: Dict[str, Any]) -> Optional[str]:
        """Extract signal type from incident data."""
        # Try multiple fields where signal type might be
        signal_type = (
            incident.get("signal_type") or
            incident.get("error") or
            incident.get("type") or
            incident.get("details", {}).get("signal_type") or
            incident.get("details", {}).get("error")
        )
        return signal_type

    def _find_matching_playbook(self, incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a matching enabled playbook for the incident."""
        signal_type = self._extract_signal_type(incident)

        if not signal_type:
            logger.warning(f"No signal_type found in incident: {incident.get('id', 'unknown')}")
            return None

        playbook = self.repository.get_enabled_playbook(signal_type)

        if playbook:
            logger.info(f"Found playbook for signal '{signal_type}': action={playbook['action']}")
        else:
            logger.info(f"No enabled playbook for signal: {signal_type}")

        return playbook

    async def execute(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate playbook for an incident."""
        incident_id = incident.get("id", incident.get("incident_id", "unknown"))
        signal_type = self._extract_signal_type(incident)

        logger.info(f"Processing incident {incident_id} with signal: {signal_type}")

        # Find matching playbook
        playbook = self._find_matching_playbook(incident)

        if not playbook:
            return {
                "incident_id": incident_id,
                "signal_type": signal_type,
                "action": "none",
                "status": "no_playbook",
                "message": f"No enabled playbook found for signal: {signal_type}",
                "executed_at": datetime.now(timezone.utc).isoformat()
            }

        # Execute the action
        action_name = playbook["action"]
        parameters = playbook.get("parameters", {})

        result: ActionResult = await self.executor.execute_action(
            action_name=action_name,
            incident=incident,
            parameters=parameters
        )

        return {
            "incident_id": incident_id,
            "signal_type": signal_type,
            "playbook_id": playbook.get("id"),
            "action": action_name,
            "status": result.status.value,
            "message": result.message,
            "executed_at": result.executed_at.isoformat(),
            "duration_ms": result.duration_ms,
            "retries": result.retries,
            "details": result.details
        }

    def execute_sync(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for execute."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute(incident))

    async def simulate(self, signal_type: str, incident_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Simulate playbook execution for testing."""
        # Create a mock incident
        incident = incident_data or {}
        incident["id"] = incident.get("id", f"test-{datetime.now().timestamp()}")
        incident["signal_type"] = signal_type

        logger.info(f"Simulating playbook for signal: {signal_type}")

        return await self.execute(incident)

    def get_playbook_for_signal(self, signal_type: str) -> Optional[Dict[str, Any]]:
        """Get the playbook that would handle a signal type."""
        return self.repository.get_enabled_playbook(signal_type)
