"""Notification Service FastAPI application."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from prometheus_fastapi_instrumentator import Instrumentator

from . import dependencies
from .application.handlers.event_handlers import (
    ProductCreatedEventHandler,
    ProductDeletedEventHandler,
    ProductUpdatedEventHandler,
    UserCreatedEventHandler,
    UserDeletedEventHandler,
    UserUpdatedEventHandler,
)
from .infrastructure.external.email_adapter import EmailServiceAdapter
from .infrastructure.external.telegram_adapter import TelegramServiceAdapter
from .infrastructure.messaging.rabbitmq_consumer import RabbitMQNotificationConsumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_HANDLER_MAP = {
    "user.created": UserCreatedEventHandler,
    "user.updated": UserUpdatedEventHandler,
    "user.deleted": UserDeletedEventHandler,
    "product.created": ProductCreatedEventHandler,
    "product.updated": ProductUpdatedEventHandler,
    "product.deleted": ProductDeletedEventHandler,
}


def _build_event_dispatcher(email_service, telegram_service, log_repo_factory):
    """Build event dispatcher using handler class mapping."""

    async def dispatch(data: dict[str, Any]) -> None:
        event_type = data.get("event_type")
        handler_cls = _HANDLER_MAP.get(event_type)
        if handler_cls:
            handler = handler_cls(email_service, telegram_service, log_repo_factory())
            await handler.handle(data)
        else:
            logger.warning(f"No handler for event type: {event_type}")

    return dispatch


def create_app() -> FastAPI:
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database_name = os.getenv("MONGODB_DATABASE", "microservices")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("FROM_EMAIL", "noreply@microservices.local")

    mongo_client = AsyncIOMotorClient(mongodb_url)
    mongo_db = mongo_client[mongodb_database_name]
    email_service = EmailServiceAdapter(smtp_host, smtp_port, smtp_user, smtp_password, from_email)
    telegram_service = TelegramServiceAdapter(telegram_bot_token, telegram_chat_id)

    dependencies.init(email_service, telegram_service, mongo_db)

    from .infrastructure.external.mongodb_adapter import MongoNotificationLogRepository
    log_repo_factory = lambda: MongoNotificationLogRepository(mongo_db)

    dispatch_event = _build_event_dispatcher(email_service, telegram_service, log_repo_factory)

    consumer_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal consumer_task
        logger.info("Starting Notification Service...")
        consumer = RabbitMQNotificationConsumer(
            rabbitmq_url=rabbitmq_url,
            event_dispatcher=dispatch_event,
        )
        consumer_task = asyncio.create_task(consumer.start())
        logger.info("Notification Service started successfully")
        yield
        logger.info("Shutting down Notification Service...")
        if consumer_task:
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        await consumer.close()
        await telegram_service.close()
        mongo_client.close()

    application = FastAPI(
        title="Notification Service",
        description="Microservice for handling notifications",
        version="2.0.0",
        lifespan=lifespan,
    )

    Instrumentator().instrument(application).expose(application)

    @application.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "notification"}

    @application.get("/status")
    async def service_status():
        return {
            "service": "notification",
            "consuming": consumer_task is not None and not consumer_task.done(),
            "subscribed_events": ["user.*", "product.*"],
            "telegram_enabled": telegram_service.enabled,
        }

    return application


app = create_app()
