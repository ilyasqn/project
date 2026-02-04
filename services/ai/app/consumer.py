"""RabbitMQ consumer for AI Service."""

import asyncio
import logging
import sys
from typing import Any

sys.path.insert(0, "/app")

from shared.rabbitmq import RabbitMQClient

from .handlers import EVENT_HANDLERS

logger = logging.getLogger(__name__)

_consumer: RabbitMQClient | None = None

QUEUE_NAME = "ai_service"
ROUTING_KEYS = [
    "product.created",
]


async def process_event(data: dict[str, Any]) -> None:
    """Process incoming event and dispatch to appropriate handler."""
    event_type = data.get("event_type")

    if not event_type:
        logger.warning(f"Received event without event_type: {data}")
        return

    handler = EVENT_HANDLERS.get(event_type)

    if handler:
        try:
            await handler(data)
            logger.info(f"Successfully processed {event_type} event")
        except Exception as e:
            logger.error(f"Error processing {event_type} event: {e}")
    else:
        logger.warning(f"No handler for event type: {event_type}")


async def get_consumer() -> RabbitMQClient:
    """Get or create consumer instance."""
    global _consumer
    if _consumer is None:
        _consumer = RabbitMQClient()
        await _consumer.connect()
    return _consumer


async def start_consuming() -> None:
    """Start consuming messages from RabbitMQ."""
    consumer = await get_consumer()

    await consumer.subscribe(
        queue_name=QUEUE_NAME,
        routing_keys=ROUTING_KEYS,
        callback=process_event,
    )

    logger.info(f"Started consuming from queue {QUEUE_NAME}")
    logger.info(f"Listening for events: {ROUTING_KEYS}")

    # Keep the consumer running
    while True:
        await asyncio.sleep(1)


async def close_consumer() -> None:
    """Close consumer connection."""
    global _consumer
    if _consumer:
        await _consumer.close()
        _consumer = None
