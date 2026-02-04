"""Redis caching for Product Service."""

import json
import logging
import os
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = 60 * 60  # 1 hour

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
        logger.info(f"Connected to Redis: {REDIS_URL}")
    return _redis


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Closed Redis connection")


def _cache_key(product_id: int) -> str:
    """Generate cache key for product."""
    return f"product:{product_id}"


async def get_cached_product(product_id: int) -> dict[str, Any] | None:
    """
    Get cached product data.

    Args:
        product_id: ID of the product

    Returns:
        Cached product data or None if not found
    """
    try:
        client = await get_redis()
        cached = await client.get(_cache_key(product_id))

        if cached:
            logger.info(f"Cache hit for product {product_id}")
            return json.loads(cached)

        logger.debug(f"Cache miss for product {product_id}")
        return None

    except Exception as e:
        logger.error(f"Redis error getting cached product: {e}")
        return None


async def cache_product(
    product_id: int,
    product_data: dict[str, Any],
    ttl: int = CACHE_TTL,
) -> bool:
    """
    Cache product data.

    Args:
        product_id: ID of the product
        product_data: The product data to cache
        ttl: Time to live in seconds (default 1 hour)

    Returns:
        True if cached successfully, False otherwise
    """
    try:
        client = await get_redis()
        await client.setex(
            _cache_key(product_id),
            ttl,
            json.dumps(product_data),
        )
        logger.info(f"Cached product {product_id} (TTL: {ttl}s)")
        return True

    except Exception as e:
        logger.error(f"Redis error caching product: {e}")
        return False


async def invalidate_product_cache(product_id: int) -> bool:
    """
    Invalidate cached product data.

    Args:
        product_id: ID of the product

    Returns:
        True if invalidated successfully, False otherwise
    """
    try:
        client = await get_redis()
        await client.delete(_cache_key(product_id))
        logger.info(f"Invalidated cache for product {product_id}")
        return True

    except Exception as e:
        logger.error(f"Redis error invalidating cache: {e}")
        return False
