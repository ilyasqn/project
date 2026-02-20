"""Product event publisher port (abstract interface).

Concrete implementation: infrastructure/messaging/rabbitmq_publisher.py -> RabbitMQProductEventPublisher
"""

from abc import ABC, abstractmethod
from typing import Any


class ProductEventPublisher(ABC):
    """Abstract interface for publishing product domain events to a message broker."""

    @abstractmethod
    async def publish(self, routing_key: str, data: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
