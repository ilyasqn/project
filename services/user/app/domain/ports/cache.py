"""User cache port (abstract interface).

Concrete implementation: infrastructure/cache/redis_adapter.py -> RedisUserCache
"""

from abc import ABC, abstractmethod
from typing import Any


class UserCache(ABC):
    """Abstract interface for user cache operations (Redis, Memcached, etc.)."""

    @abstractmethod
    async def get(self, user_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def set(self, user_id: int, data: dict[str, Any], ttl: int = 3600) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        raise NotImplementedError
