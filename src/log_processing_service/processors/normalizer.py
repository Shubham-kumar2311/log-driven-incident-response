import logging

logger = logging.getLogger("processing.normalizer")

# Maps event_type to (normalized_type, severity)
# Types needing dynamic classification are NOT in this map — they fall through to elif branches.
EVENT_TYPE_MAP = {
    # Auth service
    "auth.login_failed": ("AUTH_FAILURE", "HIGH"),
    "auth.login_success": ("AUTH_SUCCESS", "INFO"),
    # API gateway (http.request handled dynamically by status code)
    "http.health_check": ("HTTP_HEALTH_CHECK", "INFO"),
    # DB monitor (db.query handled dynamically by duration)
    "db.connection_pool": ("DB_POOL_EVENT", "LOW"),
    "db.replication_lag": ("DB_REPLICATION_LAG", "HIGH"),
    # Deployment service
    "deploy.started": ("DEPLOY_STARTED", "MEDIUM"),
    "deploy.completed": ("DEPLOY_COMPLETED", "LOW"),
    "deploy.failed": ("DEPLOY_FAILED", "CRITICAL"),
    "deploy.rollback": ("DEPLOY_ROLLBACK", "HIGH"),
    # K8s runtime
    "k8s.pod_restart": ("K8S_POD_RESTART", "HIGH"),
    "k8s.oom_kill": ("K8S_OOM_KILL", "CRITICAL"),
    "k8s.scaling": ("K8S_SCALING", "MEDIUM"),
    "k8s.node_pressure": ("K8S_NODE_PRESSURE", "HIGH"),
    "k8s.probe": ("K8S_PROBE", "INFO"),
    # Worker service
    "worker.job_completed": ("WORKER_JOB_OK", "INFO"),
    "worker.job_failed": ("WORKER_JOB_FAILED", "HIGH"),
    "worker.job_slow": ("WORKER_JOB_SLOW", "MEDIUM"),
}

LEVEL_SEVERITY = {
    "ERROR": "HIGH",
    "WARN": "MEDIUM",
    "WARNING": "MEDIUM",
    "INFO": "LOW",
    "DEBUG": "INFO",
}


class Normalizer:
    """Assign normalized_type and severity based on event_type + metadata context."""

    def process(self, event: dict) -> dict | None:
        event_type = event.get("event_type", "unknown")
        metadata = event.get("metadata") or {}
        log_level = event.get("log_level", "INFO")

        mapping = EVENT_TYPE_MAP.get(event_type)

        if mapping is not None:
            event["normalized_type"], event["severity"] = mapping

        elif event_type == "http.request":
            event["normalized_type"], event["severity"] = self._classify_http(metadata)

        elif event_type == "db.query":
            event["normalized_type"], event["severity"] = self._classify_db_query(metadata)

        else:
            event["normalized_type"] = event_type.upper().replace(".", "_")
            event["severity"] = LEVEL_SEVERITY.get(log_level, "LOW")

        # Override severity to at least HIGH if log_level is ERROR
        if log_level == "ERROR" and event["severity"] not in ("CRITICAL", "HIGH"):
            event["severity"] = "HIGH"

        return event

    @staticmethod
    def _classify_http(metadata: dict) -> tuple[str, str]:
        status = metadata.get("status_code") or metadata.get("status", 200)
        try:
            status = int(status)
        except (ValueError, TypeError):
            status = 200

        if status >= 500:
            return ("HTTP_SERVER_ERROR", "HIGH")
        elif status >= 400:
            return ("HTTP_CLIENT_ERROR", "MEDIUM")
        elif status >= 300:
            return ("HTTP_REDIRECT", "INFO")
        return ("HTTP_SUCCESS", "LOW")

    @staticmethod
    def _classify_db_query(metadata: dict) -> tuple[str, str]:
        duration = metadata.get("duration_ms", 0)
        try:
            duration = float(duration)
        except (ValueError, TypeError):
            duration = 0

        if duration > 5000:
            return ("DB_SLOW_QUERY", "HIGH")
        elif duration > 1000:
            return ("DB_SLOW_QUERY", "MEDIUM")
        return ("DB_QUERY", "LOW")