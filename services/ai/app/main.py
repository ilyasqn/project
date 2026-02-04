"""AI Service FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .consumer import close_consumer, start_consuming
from .events import close_publisher
from .mongodb import close_mongodb
from .redis_cache import close_redis
from .routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_consumer_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _consumer_task

    # Startup
    logger.info("Starting AI Service...")

    # Start RabbitMQ consumer as background task
    _consumer_task = asyncio.create_task(start_consuming())
    logger.info("Started RabbitMQ consumer task")

    logger.info("AI Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AI Service...")

    # Cancel consumer task
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    await close_consumer()
    await close_publisher()
    await close_mongodb()
    await close_redis()
    logger.info("AI Service shut down successfully")


app = FastAPI(
    title="AI Service",
    description="Microservice for AI/LLM operations",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai"}
