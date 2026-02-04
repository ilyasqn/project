"""RabbitMQ event publisher for User Service."""

import logging
import sys
from typing import Any

sys.path.insert(0, "/app")

from shared.rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)

_publisher: RabbitMQClient | None = None


async def get_publisher() -> RabbitMQClient:
    """Get or create publisher instance."""
    global _publisher
    if _publisher is None or _publisher.exchange is None:
        client = RabbitMQClient()
        await client.connect()
        _publisher = client
    return _publisher


async def close_publisher() -> None:
    """Close publisher connection."""
    global _publisher
    if _publisher:
        await _publisher.close()
        _publisher = None


async def publish_user_event(event_type: str, user_data: dict[str, Any]) -> None:
    """
    Publish user-related events.

    Args:
        event_type: Type of event (created, updated, deleted)
        user_data: User data to include in the event
    """
    publisher = await get_publisher()
    routing_key = f"user.{event_type}"

    event_payload = {
        "event_type": routing_key,
        "data": user_data,
    }

    await publisher.publish(routing_key, event_payload)
    logger.info(f"Published {routing_key} event for user {user_data.get('id')}")
