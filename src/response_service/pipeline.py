import logging
import asyncio
import json
import urllib.error
import urllib.request
from typing import Dict, Any

from engine.playbook_engine import PlaybookEngine
from messaging.consumer import IncidentConsumer
from messaging.publisher import publish_response
from config import USE_REDIS, ACTUATOR_API_URL

logger = logging.getLogger(__name__)


def _safe_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _sync_post_json(url: str, payload: Dict[str, Any], timeout: float = 8.0) -> Dict[str, Any]:
    request = urllib.request.Request(
        url=url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            raw = response.read().decode("utf-8", errors="replace")
            body = _safe_json(raw)
            return {
                "ok": 200 <= status_code < 300,
                "status_code": status_code,
                "body": body,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        body = _safe_json(raw)
        return {
            "ok": False,
            "status_code": exc.code,
            "body": body,
            "error": body.get("detail") if isinstance(body, dict) else f"HTTP {exc.code}",
        }
    except urllib.error.URLError as exc:
        reason = str(exc.reason) if getattr(exc, "reason", None) else str(exc)
        return {
            "ok": False,
            "status_code": None,
            "body": {},
            "error": reason,
        }


class ResponsePipeline:
    """Orchestrates the response service pipeline."""

    def __init__(self):
        self.engine = PlaybookEngine()
        self.consumer = IncidentConsumer(callback=self._handle_incident)
        self._running = False

    async def _forward_to_actuator(self, incident: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """Forward response action to actuator in API mode for full end-to-end chaining."""
        action = response.get("action")
        if not action or action == "none":
            return {
                "status": "skipped",
                "reason": "No executable action in response",
            }

        incident_id = response.get("incident_id", "unknown")
        details = response.get("details")
        details = details if isinstance(details, dict) else {}

        raw_parameters = details.get("parameters")
        parameters = raw_parameters if isinstance(raw_parameters, dict) else {}

        actuator_payload = {
            "incident_id": incident_id,
            "action": action,
            "parameters": parameters,
            "service_name": incident.get("service") or incident.get("affected_service"),
            "problem": response.get("signal_type") or incident.get("signal_type") or incident.get("error"),
            "detail": incident.get("details"),
        }

        actuator_url = f"{ACTUATOR_API_URL.rstrip('/')}/execute"
        result = await asyncio.to_thread(_sync_post_json, actuator_url, actuator_payload)

        if result.get("ok"):
            return {
                "status": "forwarded",
                "url": actuator_url,
                "execution": result.get("body", {}),
            }

        logger.error(
            "Failed forwarding response action to actuator: action=%s incident=%s error=%s",
            action,
            incident_id,
            result.get("error"),
        )
        return {
            "status": "failed",
            "url": actuator_url,
            "error": result.get("error"),
            "status_code": result.get("status_code"),
        }

    async def _handle_incident(self, incident: Dict[str, Any]):
        """Handle an incoming incident."""
        incident_id = incident.get("id", incident.get("incident_id", "unknown"))

        logger.info(f"Received incident: {incident_id}")

        try:
            # Execute playbook
            response = await self.engine.execute(incident)

            # Publish response event
            publish_response(response)

            logger.info(f"Processed incident {incident_id}: status={response.get('status')}")

        except Exception as e:
            logger.error(f"Error handling incident {incident_id}: {e}", exc_info=True)
            raise

    async def process_single(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single incident (for API mode)."""
        response = await self.engine.execute(incident)
        publish_response(response)

        # In API mode, there is no Redis bridge to actuator, so forward directly.
        if not USE_REDIS:
            response["actuator_forwarding"] = await self._forward_to_actuator(incident, response)

        return response

    async def start(self):
        """Start the pipeline in Redis consumer mode."""
        if not USE_REDIS:
            logger.info("Redis mode disabled, use API mode instead")
            return

        logger.info("Starting response pipeline in Redis mode")
        self._running = True

        # Process any pending messages first
        await self.consumer.process_pending()

        # Start consuming
        await self.consumer.start()

    def stop(self):
        """Stop the pipeline."""
        logger.info("Stopping response pipeline")
        self._running = False
        self.consumer.stop()


# Global pipeline instance
pipeline = ResponsePipeline()


async def process_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single incident."""
    return await pipeline.process_single(incident)


def run():
    """Run the pipeline in Redis consumer mode."""
    asyncio.run(pipeline.start())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
