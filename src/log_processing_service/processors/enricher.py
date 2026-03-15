import logging
from config import DEFAULT_REGION, DEFAULT_CLUSTER, DEFAULT_ENVIRONMENT

logger = logging.getLogger("processing.enricher")

# Risk weights by severity
SEVERITY_RISK = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.4,
    "LOW": 0.15,
    "INFO": 0.0,
}

# Extra risk boost for specific normalized types
TYPE_RISK_BOOST = {
    "AUTH_FAILURE": 0.15,
    "K8S_OOM_KILL": 0.2,
    "DEPLOY_FAILED": 0.2,
    "DEPLOY_ROLLBACK": 0.15,
    "DB_SLOW_QUERY": 0.1,
    "HTTP_SERVER_ERROR": 0.1,
    "WORKER_JOB_FAILED": 0.1,
    "K8S_POD_RESTART": 0.1,
}


class Enricher:
    """Add infrastructure context, risk score, and tags."""

    def process(self, event: dict) -> dict | None:
        # Infrastructure context
        event.setdefault("region", DEFAULT_REGION)
        event.setdefault("cluster", DEFAULT_CLUSTER)
        if not event.get("environment"):
            event["environment"] = DEFAULT_ENVIRONMENT

        severity = event.get("severity", "LOW")
        norm_type = event.get("normalized_type", "")

        # Risk score: base from severity + boost from type
        base = SEVERITY_RISK.get(severity, 0.15)
        boost = TYPE_RISK_BOOST.get(norm_type, 0.0)
        event["risk_score"] = round(min(base + boost, 1.0), 2)

        # Auto-tags
        tags = []
        if severity in ("CRITICAL", "HIGH"):
            tags.append("alert-worthy")
        if norm_type.startswith("AUTH_"):
            tags.append("security")
        if norm_type.startswith("K8S_"):
            tags.append("infrastructure")
        if norm_type.startswith("DB_"):
            tags.append("database")
        if norm_type.startswith("DEPLOY_"):
            tags.append("deployment")
        if norm_type.startswith("HTTP_"):
            tags.append("api")
        if norm_type.startswith("WORKER_"):
            tags.append("background-job")
        event["tags"] = tags

        return event