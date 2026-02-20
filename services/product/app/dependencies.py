"""Simple dependency factories for FastAPI Depends()."""

from .infrastructure.cache.redis_adapter import RedisProductCache
from .infrastructure.external.llm_adapter import OpenAILLMAdapter
from .infrastructure.external.mongodb_adapter import MongoGenerationHistoryRepository
from .infrastructure.messaging.rabbitmq_publisher import RabbitMQProductEventPublisher
from .infrastructure.persistence.uow import UnitOfWork

_session_factory = None
_redis = None
_event_publisher = None
_llm_service = None
_mongodb_database = None


def init(session_factory, redis_client, event_publisher, llm_service, mongodb_database):
    global _session_factory, _redis, _event_publisher, _llm_service, _mongodb_database
    _session_factory = session_factory
    _redis = redis_client
    _event_publisher = event_publisher
    _llm_service = llm_service
    _mongodb_database = mongodb_database


def get_uow() -> UnitOfWork:
    return UnitOfWork(_session_factory)


def get_cache() -> RedisProductCache:
    return RedisProductCache(_redis)


def get_event_publisher() -> RabbitMQProductEventPublisher:
    return _event_publisher


def get_llm_service() -> OpenAILLMAdapter:
    return _llm_service


def get_history_repo() -> MongoGenerationHistoryRepository:
    return MongoGenerationHistoryRepository(_mongodb_database)
