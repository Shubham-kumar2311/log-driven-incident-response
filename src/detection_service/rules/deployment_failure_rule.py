from models.detection_signal import DetectionSignal
from rules.base_rule import BaseRule


class DeploymentFailureRule(BaseRule):
    """Fires DEPLOYMENT_FAILURE on any deployment.failed event."""

    def check(self, event: dict) -> dict | None:
        if event.get("event_type") != "deployment.failed":
            return None

        metadata = event.get("metadata", {})

        return DetectionSignal(
            signal_type="DEPLOYMENT_FAILURE",
            severity="HIGH",
            service=event.get("service_name", "unknown"),
            metadata={
                "version": metadata.get("version"),
                "reason": metadata.get("reason"),
            },
            source="rule",
            rule_id=self.rule_id,
        ).to_dict()