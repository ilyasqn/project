"""Product Service FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from prometheus_fastapi_instrumentator import Instrumentator

from . import dependencies
from .infrastructure.external.llm_adapter import OpenAILLMAdapter
from .infrastructure.messaging.rabbitmq_publisher import RabbitMQProductEventPublisher
from .infrastructure.persistence.database import Base, create_engine, create_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/microservices")
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    llm_model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database = os.getenv("MONGODB_DATABASE", "microservices")

    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)
    redis_client = aioredis.from_url(redis_url, decode_responses=True, max_connections=20)
    event_publisher = RabbitMQProductEventPublisher(rabbitmq_url)
    llm_service = OpenAILLMAdapter(api_key=openai_api_key, base_url=openai_base_url, model=llm_model)
    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[mongodb_database]

    dependencies.init(session_factory, redis_client, event_publisher, llm_service, mongo_db)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting Product Service...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Product Service started successfully")
        yield
        logger.info("Shutting down Product Service...")
        await event_publisher.close()
        await redis_client.close()
        mongo_client.close()
        await engine.dispose()

    application = FastAPI(
        title="Product Service",
        description="Microservice for product management",
        version="2.0.0",
        lifespan=lifespan,
    )

    from .presentation.routes.product_routes import router
    application.include_router(router)

    Instrumentator().instrument(application).expose(application)

    @application.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "product"}

    return application


app = create_app()
