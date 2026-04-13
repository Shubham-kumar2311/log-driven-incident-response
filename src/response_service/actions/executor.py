import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum

from config import ACTION_TIMEOUT_SECONDS, ACTION_MAX_RETRIES, ACTION_RETRY_DELAY_SECONDS

logger = logging.getLogger(__name__)


class ActionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NO_HANDLER = "no_handler"
    RETRYING = "retrying"


class ActionResult:
    """Result of an action execution."""

    def __init__(
        self,
        incident_id: str,
        action: str,
        status: ActionStatus,
        message: str = "",
        executed_at: Optional[datetime] = None,
        duration_ms: float = 0,
        retries: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        self.incident_id = incident_id
        self.action = action
        self.status = status
        self.message = message
        self.executed_at = executed_at or datetime.now(timezone.utc)
        self.duration_ms = duration_ms
        self.retries = retries
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "action": self.action,
            "status": self.status.value,
            "message": self.message,
            "executed_at": self.executed_at.isoformat(),
            "duration_ms": round(self.duration_ms, 2),
            "retries": self.retries,
            "details": self.details
        }


def with_timeout(timeout_seconds: float):
    """Decorator to add timeout to async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Action timed out after {timeout_seconds}s")
        return wrapper
    return decorator


class ActionExecutor:
    """Executes remediation actions with retry logic and timeout protection."""

    def __init__(
        self,
        timeout_seconds: float = ACTION_TIMEOUT_SECONDS,
        max_retries: int = ACTION_MAX_RETRIES,
        retry_delay: float = ACTION_RETRY_DELAY_SECONDS
    ):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default action handlers."""
        self.register_action("restart_database", self._action_restart_database)
        self.register_action("restart_api", self._action_restart_api)
        self.register_action("lock_accounts", self._action_lock_accounts)
        self.register_action("rollback_deployment", self._action_rollback_deployment)
        self.register_action("scale_service", self._action_scale_service)
        self.register_action("restart_cache", self._action_restart_cache)
        self.register_action("notify_oncall", self._action_notify_oncall)

    def register_action(self, action_name: str, handler: Callable):
        """Register a custom action handler."""
        self._action_handlers[action_name] = handler
        logger.debug(f"Registered action handler: {action_name}")

    async def execute_action(
        self,
        action_name: str,
        incident: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """Execute an action with retry logic and timeout protection."""
        incident_id = incident.get("id", incident.get("incident_id", "unknown"))
        start_time = time.time()

        if action_name not in self._action_handlers:
            logger.warning(f"No handler for action: {action_name}")
            return ActionResult(
                incident_id=incident_id,
                action=action_name,
                status=ActionStatus.NO_HANDLER,
                message=f"No handler registered for action: {action_name}"
            )

        handler = self._action_handlers[action_name]
        last_error = None
        retries = 0

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Executing action '{action_name}' for incident {incident_id} (attempt {attempt + 1})")

                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(incident, parameters or {}),
                    timeout=self.timeout_seconds
                )

                duration_ms = (time.time() - start_time) * 1000

                logger.info(f"Action '{action_name}' completed successfully in {duration_ms:.2f}ms")

                return ActionResult(
                    incident_id=incident_id,
                    action=action_name,
                    status=ActionStatus.SUCCESS,
                    message=result.get("message", "Action completed successfully"),
                    duration_ms=duration_ms,
                    retries=retries,
                    details=result.get("details", {})
                )

            except asyncio.TimeoutError:
                last_error = f"Action timed out after {self.timeout_seconds}s"
                logger.warning(f"Action '{action_name}' timed out (attempt {attempt + 1})")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Action '{action_name}' failed: {e} (attempt {attempt + 1})")

            retries = attempt + 1

            # Don't retry on last attempt
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        duration_ms = (time.time() - start_time) * 1000

        return ActionResult(
            incident_id=incident_id,
            action=action_name,
            status=ActionStatus.TIMEOUT if "timed out" in str(last_error) else ActionStatus.FAILED,
            message=last_error or "Action failed after all retries",
            duration_ms=duration_ms,
            retries=retries
        )

    # --- Simulated Action Handlers ---

    async def _action_restart_database(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate database restart."""
        graceful = parameters.get("graceful", True)
        timeout = parameters.get("timeout", 30)

        logger.info(f"[SIMULATE] Restarting database (graceful={graceful}, timeout={timeout}s)")

        # Simulate work
        await asyncio.sleep(0.5)

        return {
            "message": f"Database restart initiated (graceful={graceful})",
            "details": {
                "service": "postgresql",
                "graceful": graceful,
                "timeout": timeout,
                "simulated": True
            }
        }

    async def _action_restart_api(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate API service restart."""
        rolling = parameters.get("rolling", True)
        batch_size = parameters.get("batch_size", 2)

        logger.info(f"[SIMULATE] Restarting API servers (rolling={rolling}, batch_size={batch_size})")

        await asyncio.sleep(0.3)

        return {
            "message": f"API servers restart initiated (rolling={rolling})",
            "details": {
                "service": "api-gateway",
                "rolling": rolling,
                "batch_size": batch_size,
                "replicas_affected": 4,
                "simulated": True
            }
        }

    async def _action_lock_accounts(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate account locking."""
        lock_duration = parameters.get("lock_duration_minutes", 30)

        # Extract IPs or accounts from incident
        source_ip = incident.get("source_ip", incident.get("details", {}).get("source_ip", "unknown"))

        logger.info(f"[SIMULATE] Locking accounts from IP {source_ip} for {lock_duration} minutes")

        await asyncio.sleep(0.2)

        return {
            "message": f"Accounts locked for IP {source_ip}",
            "details": {
                "source_ip": source_ip,
                "lock_duration_minutes": lock_duration,
                "accounts_affected": 3,
                "simulated": True
            }
        }

    async def _action_rollback_deployment(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate deployment rollback."""
        keep_logs = parameters.get("keep_logs", True)

        deployment_id = incident.get("deployment_id", incident.get("details", {}).get("deployment_id", "unknown"))

        logger.info(f"[SIMULATE] Rolling back deployment {deployment_id}")

        await asyncio.sleep(0.4)

        return {
            "message": f"Deployment {deployment_id} rolled back",
            "details": {
                "deployment_id": deployment_id,
                "previous_version": "v1.2.3",
                "keep_logs": keep_logs,
                "simulated": True
            }
        }

    async def _action_scale_service(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate service scaling."""
        scale_factor = parameters.get("scale_factor", 2)
        max_instances = parameters.get("max_instances", 10)

        service = incident.get("service", incident.get("details", {}).get("service", "api-service"))

        logger.info(f"[SIMULATE] Scaling service {service} by factor {scale_factor}")

        await asyncio.sleep(0.3)

        return {
            "message": f"Service {service} scaled",
            "details": {
                "service": service,
                "scale_factor": scale_factor,
                "previous_replicas": 2,
                "new_replicas": min(4, max_instances),
                "simulated": True
            }
        }

    async def _action_restart_cache(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate cache restart."""
        flush_on_restart = parameters.get("flush_on_restart", False)

        logger.info(f"[SIMULATE] Restarting cache (flush={flush_on_restart})")

        await asyncio.sleep(0.2)

        return {
            "message": f"Cache restarted (flush={flush_on_restart})",
            "details": {
                "service": "redis",
                "flush_on_restart": flush_on_restart,
                "simulated": True
            }
        }

    async def _action_notify_oncall(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate on-call notification."""
        channel = parameters.get("channel", "slack")

        logger.info(f"[SIMULATE] Notifying on-call via {channel}")

        await asyncio.sleep(0.1)

        return {
            "message": f"On-call notified via {channel}",
            "details": {
                "channel": channel,
                "incident_id": incident.get("id", "unknown"),
                "simulated": True
            }
        }


# Global executor instance
executor = ActionExecutor()


async def execute_action(
    action_name: str,
    incident: Dict[str, Any],
    parameters: Optional[Dict[str, Any]] = None
) -> ActionResult:
    """Convenience function to execute an action."""
    return await executor.execute_action(action_name, incident, parameters)
