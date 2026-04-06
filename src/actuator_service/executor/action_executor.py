"""
Action Executor - Multi-mode execution engine for actuator service.

Supports three execution modes:
1. Subprocess mode (default) - Execute shell commands
2. Docker mode - Restart containers via docker CLI
3. Service-call mode - Call external REST APIs

Implements retry mechanism, timeout handling, and structured logging.
"""
import asyncio
import logging
import subprocess
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional
import httpx

import sys
sys.path.insert(0, str(__file__).rsplit("/", 1)[0].rsplit("\\", 1)[0])
from config import (
    USE_DOCKER,
    EXECUTION_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    DOCKER_DB_CONTAINER,
    DOCKER_API_CONTAINER,
    DOCKER_CACHE_CONTAINER,
    DOCKER_WORKER_CONTAINER,
    SERVICE_API_BASE,
    AUTH_SERVICE_URL,
)

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NO_HANDLER = "no_handler"
    RETRYING = "retrying"


class ExecutionMode(str, Enum):
    SUBPROCESS = "subprocess"
    DOCKER = "docker"
    SERVICE_CALL = "service_call"


class ExecutionResult:
    """Structured result of an action execution."""

    def __init__(
        self,
        incident_id: str,
        action: str,
        execution_status: ExecutionStatus,
        output: str = "",
        executed_at: Optional[datetime] = None,
        duration_ms: float = 0,
        retries: int = 0,
        mode: ExecutionMode = ExecutionMode.SUBPROCESS,
        details: Optional[Dict[str, Any]] = None
    ):
        self.incident_id = incident_id
        self.action = action
        self.execution_status = execution_status
        self.output = output
        self.executed_at = executed_at or datetime.now(timezone.utc)
        self.duration_ms = duration_ms
        self.retries = retries
        self.mode = mode
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "action": self.action,
            "execution_status": self.execution_status.value,
            "output": self.output,
            "executed_at": self.executed_at.isoformat(),
            "duration_ms": round(self.duration_ms, 2),
            "retries": self.retries,
            "mode": self.mode.value,
            "details": self.details
        }


class ActionExecutor:
    """Multi-mode execution engine with retry and timeout support."""

    def __init__(
        self,
        timeout_seconds: float = EXECUTION_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
        use_docker: bool = USE_DOCKER
    ):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_docker = use_docker
        self._action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default action handlers."""
        self.register_action("restart_database", self._action_restart_database)
        self.register_action("restart_api", self._action_restart_api)
        self.register_action("restart_server", self._action_restart_server)
        self.register_action("restart_cache", self._action_restart_cache)
        self.register_action("restart_worker", self._action_restart_worker)
        self.register_action("lock_accounts", self._action_lock_accounts)
        self.register_action("unlock_accounts", self._action_unlock_accounts)
        self.register_action("scale_service", self._action_scale_service)
        self.register_action("rollback_deployment", self._action_rollback_deployment)
        self.register_action("clear_cache", self._action_clear_cache)
        self.register_action("notify_oncall", self._action_notify_oncall)

    def register_action(self, action_name: str, handler: Callable):
        """Register a custom action handler."""
        self._action_handlers[action_name] = handler
        logger.debug(f"Registered action handler: {action_name}")

    def get_registered_actions(self) -> list:
        """Get list of all registered actions."""
        return list(self._action_handlers.keys())

    async def execute_action(
        self,
        action_name: str,
        incident: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute an action with retry logic and timeout protection.

        Args:
            action_name: Name of the action to execute
            incident: Incident data containing id and context
            parameters: Optional parameters for the action

        Returns:
            ExecutionResult with status, output, and metadata
        """
        incident_id = incident.get("id", incident.get("incident_id", "unknown"))
        start_time = time.time()
        params = parameters or {}

        logger.info(f"Starting execution: action={action_name}, incident={incident_id}")

        if action_name not in self._action_handlers:
            logger.warning(f"No handler for action: {action_name}")
            return ExecutionResult(
                incident_id=incident_id,
                action=action_name,
                execution_status=ExecutionStatus.NO_HANDLER,
                output=f"No handler registered for action: {action_name}",
                duration_ms=(time.time() - start_time) * 1000
            )

        handler = self._action_handlers[action_name]
        last_error = None
        retries = 0

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"Executing '{action_name}' for incident {incident_id} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )

                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(incident, params),
                    timeout=self.timeout_seconds
                )

                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"Action '{action_name}' completed successfully in {duration_ms:.2f}ms"
                )

                return ExecutionResult(
                    incident_id=incident_id,
                    action=action_name,
                    execution_status=ExecutionStatus.SUCCESS,
                    output=result.get("output", "Action completed successfully"),
                    duration_ms=duration_ms,
                    retries=retries,
                    mode=result.get("mode", ExecutionMode.SUBPROCESS),
                    details=result.get("details", {})
                )

            except asyncio.TimeoutError:
                last_error = f"Action timed out after {self.timeout_seconds}s"
                logger.warning(f"Action '{action_name}' timed out (attempt {attempt + 1})")

            except subprocess.CalledProcessError as e:
                last_error = f"Command failed with exit code {e.returncode}: {e.stderr}"
                logger.error(f"Action '{action_name}' subprocess error: {last_error}")

            except httpx.HTTPError as e:
                last_error = f"HTTP error: {str(e)}"
                logger.error(f"Action '{action_name}' HTTP error: {last_error}")

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

        return ExecutionResult(
            incident_id=incident_id,
            action=action_name,
            execution_status=ExecutionStatus.TIMEOUT if "timed out" in str(last_error) else ExecutionStatus.FAILED,
            output=last_error or "Action failed after all retries",
            duration_ms=duration_ms,
            retries=retries
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Subprocess Execution Helper
    # ──────────────────────────────────────────────────────────────────────────

    async def _run_subprocess(
        self,
        command: list,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute a subprocess command and capture output."""
        timeout = timeout or self.timeout_seconds

        logger.debug(f"Running subprocess: {' '.join(command)}")

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        stdout_str = stdout.decode().strip() if stdout else ""
        stderr_str = stderr.decode().strip() if stderr else ""

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                command,
                stdout_str,
                stderr_str
            )

        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "returncode": process.returncode
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Docker Execution Helper
    # ──────────────────────────────────────────────────────────────────────────

    async def _docker_restart(self, container_name: str) -> Dict[str, Any]:
        """Restart a Docker container."""
        logger.info(f"Docker restart: {container_name}")
        result = await self._run_subprocess(["docker", "restart", container_name])
        return {
            "output": f"Container '{container_name}' restarted successfully",
            "mode": ExecutionMode.DOCKER,
            "details": {
                "container": container_name,
                "stdout": result["stdout"]
            }
        }

    async def _docker_stop(self, container_name: str) -> Dict[str, Any]:
        """Stop a Docker container."""
        logger.info(f"Docker stop: {container_name}")
        result = await self._run_subprocess(["docker", "stop", container_name])
        return {
            "output": f"Container '{container_name}' stopped",
            "mode": ExecutionMode.DOCKER,
            "details": {"container": container_name, "stdout": result["stdout"]}
        }

    async def _docker_start(self, container_name: str) -> Dict[str, Any]:
        """Start a Docker container."""
        logger.info(f"Docker start: {container_name}")
        result = await self._run_subprocess(["docker", "start", container_name])
        return {
            "output": f"Container '{container_name}' started",
            "mode": ExecutionMode.DOCKER,
            "details": {"container": container_name, "stdout": result["stdout"]}
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Service Call Helper
    # ──────────────────────────────────────────────────────────────────────────

    async def _service_call(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Make an HTTP service call."""
        timeout = timeout or self.timeout_seconds
        logger.info(f"Service call: {method} {url}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_data
            )
            response.raise_for_status()

            return {
                "output": f"Service call successful: {method} {url}",
                "mode": ExecutionMode.SERVICE_CALL,
                "details": {
                    "url": url,
                    "status_code": response.status_code,
                    "response": response.json() if response.content else {}
                }
            }

    # ══════════════════════════════════════════════════════════════════════════
    # ACTION HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    async def _action_restart_database(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restart database - subprocess/docker mode."""
        container = parameters.get("container", DOCKER_DB_CONTAINER)

        if self.use_docker:
            return await self._docker_restart(container)
        else:
            # Subprocess simulation mode - safe echo command
            result = await self._run_subprocess([
                "echo", f"[ACTUATOR] Restarting database service: {container}"
            ])
            return {
                "output": f"Database restart command executed for '{container}'",
                "mode": ExecutionMode.SUBPROCESS,
                "details": {
                    "service": "database",
                    "container": container,
                    "simulated": not self.use_docker,
                    "stdout": result["stdout"]
                }
            }

    async def _action_restart_api(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restart API service - subprocess/docker/service-call mode."""
        container = parameters.get("container", DOCKER_API_CONTAINER)
        use_api = parameters.get("use_api", False)

        if use_api:
            # Service call mode
            url = f"{SERVICE_API_BASE}/admin/restart"
            return await self._service_call("POST", url)
        elif self.use_docker:
            return await self._docker_restart(container)
        else:
            result = await self._run_subprocess([
                "echo", f"[ACTUATOR] Restarting API service: {container}"
            ])
            return {
                "output": f"API restart command executed for '{container}'",
                "mode": ExecutionMode.SUBPROCESS,
                "details": {
                    "service": "api",
                    "container": container,
                    "simulated": True,
                    "stdout": result["stdout"]
                }
            }

    async def _action_restart_server(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restart server - subprocess mode with safe commands."""
        server_name = parameters.get("server", "app-server")

        result = await self._run_subprocess([
            "echo", f"[ACTUATOR] Restarting server: {server_name}"
        ])
        return {
            "output": f"Server restart command executed for '{server_name}'",
            "mode": ExecutionMode.SUBPROCESS,
            "details": {
                "server": server_name,
                "simulated": True,
                "stdout": result["stdout"]
            }
        }

    async def _action_restart_cache(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restart cache service (Redis/Memcached)."""
        container = parameters.get("container", DOCKER_CACHE_CONTAINER)
        flush = parameters.get("flush", False)

        if self.use_docker:
            result = await self._docker_restart(container)
            result["details"]["flush"] = flush
            return result
        else:
            result = await self._run_subprocess([
                "echo", f"[ACTUATOR] Restarting cache service: {container} (flush={flush})"
            ])
            return {
                "output": f"Cache restart command executed for '{container}'",
                "mode": ExecutionMode.SUBPROCESS,
                "details": {
                    "service": "cache",
                    "container": container,
                    "flush": flush,
                    "simulated": True,
                    "stdout": result["stdout"]
                }
            }

    async def _action_restart_worker(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restart worker service."""
        container = parameters.get("container", DOCKER_WORKER_CONTAINER)

        if self.use_docker:
            return await self._docker_restart(container)
        else:
            result = await self._run_subprocess([
                "echo", f"[ACTUATOR] Restarting worker service: {container}"
            ])
            return {
                "output": f"Worker restart command executed for '{container}'",
                "mode": ExecutionMode.SUBPROCESS,
                "details": {
                    "service": "worker",
                    "container": container,
                    "simulated": True,
                    "stdout": result["stdout"]
                }
            }

    async def _action_lock_accounts(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lock user accounts - service call or subprocess."""
        source_ip = parameters.get("source_ip", incident.get("source_ip", "unknown"))
        lock_duration = parameters.get("lock_duration_minutes", 30)
        use_api = parameters.get("use_api", False)

        if use_api:
            url = f"{AUTH_SERVICE_URL}/admin/lock-accounts"
            return await self._service_call("POST", url, {
                "source_ip": source_ip,
                "lock_duration_minutes": lock_duration
            })
        else:
            result = await self._run_subprocess([
                "echo", f"[ACTUATOR] Locking accounts for IP {source_ip} ({lock_duration} min)"
            ])
            return {
                "output": f"Accounts locked for IP {source_ip} for {lock_duration} minutes",
                "mode": ExecutionMode.SUBPROCESS,
                "details": {
                    "action": "lock_accounts",
                    "source_ip": source_ip,
                    "lock_duration_minutes": lock_duration,
                    "simulated": True,
                    "stdout": result["stdout"]
                }
            }

    async def _action_unlock_accounts(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Unlock user accounts."""
        source_ip = parameters.get("source_ip", incident.get("source_ip", "unknown"))
        use_api = parameters.get("use_api", False)

        if use_api:
            url = f"{AUTH_SERVICE_URL}/admin/unlock-accounts"
            return await self._service_call("POST", url, {"source_ip": source_ip})
        else:
            result = await self._run_subprocess([
                "echo", f"[ACTUATOR] Unlocking accounts for IP {source_ip}"
            ])
            return {
                "output": f"Accounts unlocked for IP {source_ip}",
                "mode": ExecutionMode.SUBPROCESS,
                "details": {
                    "action": "unlock_accounts",
                    "source_ip": source_ip,
                    "simulated": True,
                    "stdout": result["stdout"]
                }
            }

    async def _action_scale_service(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scale a service up or down."""
        service = parameters.get("service", "api")
        scale_factor = parameters.get("scale_factor", 2)
        replicas = parameters.get("replicas", None)

        result = await self._run_subprocess([
            "echo", f"[ACTUATOR] Scaling service {service} by factor {scale_factor}"
        ])
        return {
            "output": f"Service {service} scaled by factor {scale_factor}",
            "mode": ExecutionMode.SUBPROCESS,
            "details": {
                "service": service,
                "scale_factor": scale_factor,
                "replicas": replicas,
                "simulated": True,
                "stdout": result["stdout"]
            }
        }

    async def _action_rollback_deployment(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rollback to previous deployment."""
        deployment_id = parameters.get(
            "deployment_id",
            incident.get("deployment_id", "unknown")
        )
        target_version = parameters.get("target_version", "previous")

        result = await self._run_subprocess([
            "echo", f"[ACTUATOR] Rolling back deployment {deployment_id} to {target_version}"
        ])
        return {
            "output": f"Deployment {deployment_id} rolled back to {target_version}",
            "mode": ExecutionMode.SUBPROCESS,
            "details": {
                "deployment_id": deployment_id,
                "target_version": target_version,
                "simulated": True,
                "stdout": result["stdout"]
            }
        }

    async def _action_clear_cache(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Clear application cache."""
        cache_type = parameters.get("cache_type", "all")
        pattern = parameters.get("pattern", "*")

        result = await self._run_subprocess([
            "echo", f"[ACTUATOR] Clearing cache: type={cache_type}, pattern={pattern}"
        ])
        return {
            "output": f"Cache cleared: type={cache_type}, pattern={pattern}",
            "mode": ExecutionMode.SUBPROCESS,
            "details": {
                "cache_type": cache_type,
                "pattern": pattern,
                "simulated": True,
                "stdout": result["stdout"]
            }
        }

    async def _action_notify_oncall(
        self,
        incident: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Notify on-call team."""
        channel = parameters.get("channel", "slack")
        priority = parameters.get("priority", "high")
        incident_id = incident.get("id", incident.get("incident_id", "unknown"))

        result = await self._run_subprocess([
            "echo", f"[ACTUATOR] Notifying on-call via {channel} (priority={priority})"
        ])
        return {
            "output": f"On-call notified via {channel} for incident {incident_id}",
            "mode": ExecutionMode.SUBPROCESS,
            "details": {
                "channel": channel,
                "priority": priority,
                "incident_id": incident_id,
                "simulated": True,
                "stdout": result["stdout"]
            }
        }


# Global executor instance
executor = ActionExecutor()


async def execute_action(
    action_name: str,
    incident: Dict[str, Any],
    parameters: Optional[Dict[str, Any]] = None
) -> ExecutionResult:
    """Convenience function to execute an action."""
    return await executor.execute_action(action_name, incident, parameters)
