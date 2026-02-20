"""RabbitMQ implementation of ProductEventPublisher."""

import logging
import sys
from typing import Any

sys.path.insert(0, "/app")

from shared.rabbitmq import RabbitMQClient

from ...domain.ports.event_publisher import ProductEventPublisher

logger = logging.getLogger(__name__)


class RabbitMQProductEventPublisher(ProductEventPublisher):
    def __init__(self, rabbitmq_url: str):
        self._url = rabbitmq_url
        self._client: RabbitMQClient | None = None

    async def _get_client(self) -> RabbitMQClient:
        if self._client is None or self._client.exchange is None:
            self._client = RabbitMQClient(url=self._url)
            await self._client.connect()
        return self._client

    async def publish(self, routing_key: str, data: dict[str, Any]) -> None:
        client = await self._get_client()
        await client.publish(routing_key, data)
        logger.info(f"Published {routing_key} event")

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
