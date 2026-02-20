"""Simple dependency factories for FastAPI Depends().

No framework needed — just functions that return instances.
Singletons are initialized once at startup via init().
"""

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from .infrastructure.cache.redis_adapter import RedisUserCache
from .infrastructure.messaging.rabbitmq_publisher import RabbitMQUserEventPublisher
from .infrastructure.persistence.uow import UnitOfWork

# App-level singletons (set once at startup)
_session_factory: async_sessionmaker[AsyncSession] | None = None
_redis: aioredis.Redis | None = None
_event_publisher: RabbitMQUserEventPublisher | None = None


def init(session_factory, redis_client, event_publisher):
    """Called once at app startup to set shared resources."""
    global _session_factory, _redis, _event_publisher
    _session_factory = session_factory
    _redis = redis_client
    _event_publisher = event_publisher


def get_uow() -> UnitOfWork:
    return UnitOfWork(_session_factory)


def get_cache() -> RedisUserCache:
    return RedisUserCache(_redis)


def get_event_publisher() -> RabbitMQUserEventPublisher:
    return _event_publisher
