"""User event publisher port (abstract interface).

Concrete implementation: infrastructure/messaging/rabbitmq_publisher.py -> RabbitMQUserEventPublisher
"""

from abc import ABC, abstractmethod
from typing import Any


class UserEventPublisher(ABC):
    """Abstract interface for publishing user domain events to a message broker."""

    @abstractmethod
    async def publish(self, routing_key: str, data: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
