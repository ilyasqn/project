"""User Service FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .database import init_db
from .events import close_publisher, get_publisher
from .routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting User Service...")
    await init_db()
    # RabbitMQ connection is lazy - don't block startup
    logger.info("User Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down User Service...")
    await close_publisher()
    logger.info("User Service shut down successfully")


app = FastAPI(
    title="User Service",
    description="Microservice for user management",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "user"}
