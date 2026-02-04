"""Notification Service FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .consumer import close_consumer, start_consuming
from .mongodb import close_mongodb
from .telegram import telegram_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global consumer_task

    # Startup
    logger.info("Starting Notification Service...")

    # Start consumer in background
    consumer_task = asyncio.create_task(start_consuming())
    logger.info("Notification Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Notification Service...")
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    await close_consumer()
    await telegram_service.close()
    await close_mongodb()
    logger.info("Notification Service shut down successfully")


app = FastAPI(
    title="Notification Service",
    description="Microservice for handling notifications",
    version="1.0.0",
    lifespan=lifespan,
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notification"}


@app.get("/status")
async def status():
    """Get service status."""
    return {
        "service": "notification",
        "consuming": consumer_task is not None and not consumer_task.done(),
        "subscribed_events": ["user.*", "product.*", "ai.*"],
        "telegram_enabled": telegram_service.enabled,
    }
