"""Product cache port (abstract interface).

Concrete implementation: infrastructure/cache/redis_adapter.py -> RedisProductCache
"""

from abc import ABC, abstractmethod
from typing import Any


class ProductCache(ABC):
    """Abstract interface for product cache operations."""

    @abstractmethod
    async def get(self, product_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def set(self, product_id: int, data: dict[str, Any], ttl: int = 3600) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, product_id: int) -> None:
        raise NotImplementedError
