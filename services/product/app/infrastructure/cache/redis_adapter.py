"""Redis implementation of ProductCache."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from ...domain.ports.cache import ProductCache

logger = logging.getLogger(__name__)


class RedisProductCache(ProductCache):
    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client

    def _key(self, product_id: int) -> str:
        return f"product:{product_id}"

    async def get(self, product_id: int) -> dict[str, Any] | None:
        try:
            cached = await self._redis.get(self._key(product_id))
            if cached:
                logger.info(f"Cache hit for product {product_id}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, product_id: int, data: dict[str, Any], ttl: int = 3600) -> None:
        try:
            await self._redis.setex(self._key(product_id), ttl, json.dumps(data))
            logger.info(f"Cached product {product_id} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, product_id: int) -> None:
        try:
            await self._redis.delete(self._key(product_id))
            logger.info(f"Invalidated cache for product {product_id}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
