import logging
import asyncio
from typing import Dict, Any

from engine.playbook_engine import PlaybookEngine
from messaging.consumer import IncidentConsumer
from messaging.publisher import publish_response
from config import USE_REDIS

logger = logging.getLogger(__name__)


class ResponsePipeline:
    """Orchestrates the response service pipeline."""

    def __init__(self):
        self.engine = PlaybookEngine()
        self.consumer = IncidentConsumer(callback=self._handle_incident)
        self._running = False

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
