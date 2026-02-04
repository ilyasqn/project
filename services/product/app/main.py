"""Product Service FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .consumer import close_consumer, start_consuming
from .database import init_db
from .events import close_publisher
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
    logger.info("Starting Product Service...")
    await init_db()

    # Start RabbitMQ consumer as background task
    _consumer_task = asyncio.create_task(start_consuming())
    logger.info("Started RabbitMQ consumer task")

    logger.info("Product Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Product Service...")

    # Cancel consumer task
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    await close_consumer()
    await close_publisher()
    await close_redis()
    logger.info("Product Service shut down successfully")


app = FastAPI(
    title="Product Service",
    description="Microservice for product management",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "product"}
