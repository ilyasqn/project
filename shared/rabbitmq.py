"""Shared RabbitMQ utilities for pub/sub messaging."""

import asyncio
import json
import logging
import os
from typing import Any, Callable, Coroutine

import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "events"


class RabbitMQClient:
    """RabbitMQ client for publishing and consuming messages."""

    def __init__(self, url: str = RABBITMQ_URL):
        self.url = url
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None
        self.exchange: aio_pika.Exchange | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    EXCHANGE_NAME,
                    ExchangeType.TOPIC,
                    durable=True,
                )
                logger.info("Connected to RabbitMQ")
                return
            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {e}"
                )
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)
                else:
                    raise

    async def close(self) -> None:
        """Close connection to RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish(self, routing_key: str, data: dict[str, Any]) -> None:
        """
        Publish a message to the exchange.

        Args:
            routing_key: Topic routing key (e.g., "user.created", "product.updated")
            data: Message payload as dictionary
        """
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")

        message = Message(
            body=json.dumps(data).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self.exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published message to {routing_key}: {data}")

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Subscribe to messages matching routing keys.

        Args:
            queue_name: Name of the queue to create/use
            routing_keys: List of routing key patterns to subscribe to
            callback: Async function to call for each message
        """
        if not self.channel or not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")

        queue = await self.channel.declare_queue(queue_name, durable=True)

        for routing_key in routing_keys:
            await queue.bind(self.exchange, routing_key=routing_key)
            logger.info(f"Bound queue {queue_name} to routing key {routing_key}")

        async def process_message(message: AbstractIncomingMessage) -> None:
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    logger.info(
                        f"Received message on {message.routing_key}: {data}"
                    )
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        await queue.consume(process_message)
        logger.info(f"Started consuming from queue {queue_name}")


# Singleton instance
_rabbitmq_client: RabbitMQClient | None = None


async def get_rabbitmq_client() -> RabbitMQClient:
    """Get or create RabbitMQ client singleton."""
    global _rabbitmq_client
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient()
        await _rabbitmq_client.connect()
    return _rabbitmq_client
