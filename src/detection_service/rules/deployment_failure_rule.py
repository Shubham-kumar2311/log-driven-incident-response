from models.detection_signal import DetectionSignal


class DeploymentFailureRule:

    def check(self, event):

        if event.get("event_type") != "deployment.failed":
            return None

        metadata = event.get("metadata", {})

        return DetectionSignal(
            "DEPLOYMENT_FAILURE",
            "HIGH",
            event.get("service_name"),
            {
                "version": metadata.get("version"),
                "reason": metadata.get("reason")
            }
        ).to_dict()