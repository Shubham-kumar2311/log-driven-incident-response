"""
Actuator Service Pipeline.

Orchestrates the execution flow:
1. Receive response events (from Redis or API)
2. Execute actions via ActionExecutor
3. Publish results to actuator_events stream
4. Store execution history
"""
import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional

from executor.action_executor import ActionExecutor, ExecutionResult, execute_action
from messaging.publisher import publish_event
from config import MAX_HISTORY_SIZE

logger = logging.getLogger(__name__)


class ExecutionHistory:
    """Thread-safe execution history store."""

    def __init__(self, max_size: int = MAX_HISTORY_SIZE):
        self._history: deque = deque(maxlen=max_size)
        self._lock = RLock()
        self._counters = {
            "total_executions": 0,
            "success_count": 0,
            "failed_count": 0,
            "timeout_count": 0
        }

    def add(self, result: ExecutionResult, extra: Optional[Dict[str, Any]] = None):
        """Add an execution result to history."""
        with self._lock:
            record = result.to_dict()
            if isinstance(extra, dict):
                for key, value in extra.items():
                    if value is not None:
                        record[key] = value

            self._history.appendleft(record)
            self._counters["total_executions"] += 1

            status = result.execution_status.value
            if status == "success":
                self._counters["success_count"] += 1
            elif status == "failed":
                self._counters["failed_count"] += 1
            elif status == "timeout":
                self._counters["timeout_count"] += 1

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution results."""
        with self._lock:
            return list(self._history)[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        with self._lock:
            return {
                **self._counters,
                "history_size": len(self._history)
            }

    def clear(self):
        """Clear execution history."""
        with self._lock:
            self._history.clear()
            self._counters = {
                "total_executions": 0,
                "success_count": 0,
                "failed_count": 0,
                "timeout_count": 0
            }


class ActuatorPipeline:
    """Main pipeline for processing response events and executing actions."""

    def __init__(self):
        self.executor = ActionExecutor()
        self.history = ExecutionHistory()
        self._start_time = datetime.now(timezone.utc)

    async def process_event(self, event: Dict[str, Any]) -> ExecutionResult:
        """
        Process a response event and execute the associated action.

        Args:
            event: Response event containing action and incident data

        Returns:
            ExecutionResult with status and output
        """
        # Extract action and incident from event
        action = event.get("action", event.get("action_name"))
        incident_id = event.get("incident_id", event.get("id", "unknown"))
        parameters = event.get("parameters", {})

        # Build incident dict for executor
        incident = {
            "id": incident_id,
            "incident_id": incident_id,
            **event
        }

        context = {
            "service_name": event.get("service") or event.get("service_name"),
            "problem": event.get("signal_type") or event.get("error") or event.get("type"),
            "detail": event.get("details"),
            "actuator_received_payload": event,
        }

        if not action:
            logger.warning(f"No action specified in event: {event}")
            result = ExecutionResult(
                incident_id=incident_id,
                action="unknown",
                execution_status="failed",
                output="No action specified in event"
            )
            self.history.add(result, extra=context)
            publish_event({
                **result.to_dict(),
                "solution": result.output,
                "signal_type": event.get("signal_type") or event.get("error") or event.get("type"),
                "event_details": event.get("details", {}),
                "source_event": event,
            })
            return result

        logger.info(f"Processing event: action={action}, incident={incident_id}")

        # Execute the action
        result = await self.executor.execute_action(action, incident, parameters)

        # Store in history
        self.history.add(result, extra=context)

        # Publish to Redis stream with event context for downstream UIs.
        publish_event({
            **result.to_dict(),
            "solution": result.output,
            "signal_type": event.get("signal_type") or event.get("error") or event.get("type"),
            "event_details": event.get("details", {}),
            "source_event": event,
        })

        logger.info(
            f"Execution complete: action={action}, status={result.execution_status.value}, "
            f"duration={result.duration_ms:.2f}ms"
        )

        return result

    async def execute_direct(
        self,
        action: str,
        incident_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute an action directly (for API calls).

        Args:
            action: Action name to execute
            incident_id: Incident ID
            parameters: Optional parameters

        Returns:
            ExecutionResult
        """
        incident = {"id": incident_id, "incident_id": incident_id}
        result = await self.executor.execute_action(action, incident, parameters)

        # Store and publish
        self.history.add(result, extra=context)
        publish_event({
            **result.to_dict(),
            "solution": result.output,
            "service_name": context.get("service_name") if isinstance(context, dict) else None,
            "problem": context.get("problem") if isinstance(context, dict) else None,
            "detail": context.get("detail") if isinstance(context, dict) else None,
        })

        return result

    def get_health(self) -> Dict[str, Any]:
        """Get pipeline health status."""
        stats = self.history.get_stats()
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        return {
            "status": "healthy",
            "uptime_seconds": round(uptime, 2),
            "registered_actions": self.executor.get_registered_actions(),
            "action_count": len(self.executor.get_registered_actions()),
            "executions": stats
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics."""
        stats = self.history.get_stats()
        uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        success_rate = 0
        if stats["total_executions"] > 0:
            success_rate = (stats["success_count"] / stats["total_executions"]) * 100

        return {
            "total_executions": stats["total_executions"],
            "success_count": stats["success_count"],
            "failed_count": stats["failed_count"],
            "timeout_count": stats["timeout_count"],
            "success_rate_percent": round(success_rate, 2),
            "uptime_seconds": round(uptime, 2),
            "executions_per_minute": round(
                stats["total_executions"] / max(uptime / 60, 1), 2
            )
        }


# Global pipeline instance
pipeline = ActuatorPipeline()


async def handle_response_event(event: Dict[str, Any]) -> ExecutionResult:
    """Handler function for Redis consumer."""
    return await pipeline.process_event(event)
