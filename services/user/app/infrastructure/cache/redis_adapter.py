"""Redis implementation of UserCache."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from ...domain.ports.cache import UserCache

logger = logging.getLogger(__name__)


class RedisUserCache(UserCache):
    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client

    def _key(self, user_id: int) -> str:
        return f"user:{user_id}"

    async def get(self, user_id: int) -> dict[str, Any] | None:
        try:
            cached = await self._redis.get(self._key(user_id))
            if cached:
                logger.info(f"Cache hit for user {user_id}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, user_id: int, data: dict[str, Any], ttl: int = 3600) -> None:
        try:
            await self._redis.setex(self._key(user_id), ttl, json.dumps(data))
            logger.info(f"Cached user {user_id} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, user_id: int) -> None:
        try:
            await self._redis.delete(self._key(user_id))
            logger.info(f"Invalidated cache for user {user_id}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
