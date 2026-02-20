"""RabbitMQ consumer for Notification Service."""

import asyncio
import logging
import sys
from typing import Any, Callable, Coroutine

sys.path.insert(0, "/app")

from shared.rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)

QUEUE_NAME = "notification_service"
ROUTING_KEYS = [
    "user.*",
    "product.*",
]


class RabbitMQNotificationConsumer:
    def __init__(self, rabbitmq_url: str, event_dispatcher: Callable[[dict[str, Any]], Coroutine]):
        self._url = rabbitmq_url
        self._client: RabbitMQClient | None = None
        self._dispatcher = event_dispatcher

    async def start(self) -> None:
        self._client = RabbitMQClient(url=self._url)
        await self._client.connect()

        await self._client.subscribe(
            queue_name=QUEUE_NAME,
            routing_keys=ROUTING_KEYS,
            callback=self._process_event,
        )

        logger.info(f"Started consuming from queue {QUEUE_NAME}")
        logger.info(f"Listening for events: {ROUTING_KEYS}")

        while True:
            await asyncio.sleep(1)

    async def _process_event(self, data: dict[str, Any]) -> None:
        event_type = data.get("event_type")
        if not event_type:
            logger.warning(f"Received event without event_type: {data}")
            return

        try:
            await self._dispatcher(data)
            logger.info(f"Successfully processed {event_type} event")
        except Exception as e:
            logger.error(f"Error processing {event_type} event: {e}")

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
