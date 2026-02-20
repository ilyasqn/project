"""User Service FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from . import dependencies
from .infrastructure.messaging.rabbitmq_publisher import RabbitMQUserEventPublisher
from .infrastructure.persistence.database import Base, create_engine, create_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/microservices")
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)
    redis_client = aioredis.from_url(redis_url, decode_responses=True, max_connections=20)
    event_publisher = RabbitMQUserEventPublisher(rabbitmq_url)

    dependencies.init(session_factory, redis_client, event_publisher)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting User Service...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("User Service started")
        yield
        logger.info("Shutting down User Service...")
        await event_publisher.close()
        await redis_client.close()
        await engine.dispose()

    application = FastAPI(
        title="User Service",
        description="Microservice for user management",
        version="2.0.0",
        lifespan=lifespan,
    )

    from .presentation.routes.user_routes import router
    application.include_router(router)

    Instrumentator().instrument(application).expose(application)

    @application.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "user"}

    return application


app = create_app()
