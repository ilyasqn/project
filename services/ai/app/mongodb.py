"""MongoDB client for AI Service generation history."""

import logging
import os
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "microservices")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def get_mongodb() -> AsyncIOMotorDatabase:
    """Get or create MongoDB database instance."""
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URL)
        _db = _client[MONGODB_DATABASE]
        logger.info(f"Connected to MongoDB: {MONGODB_DATABASE}")
    return _db


async def close_mongodb() -> None:
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("Closed MongoDB connection")


async def save_generation_history(
    product_id: int,
    product_name: str,
    prompt: str,
    description: str,
    tokens_used: int | None = None,
) -> str:
    """
    Save AI generation history to MongoDB.

    Args:
        product_id: ID of the product
        product_name: Name of the product
        prompt: The prompt used for generation
        description: The generated description
        tokens_used: Number of tokens used (optional)

    Returns:
        ID of the inserted document
    """
    db = await get_mongodb()

    document = {
        "product_id": product_id,
        "product_name": product_name,
        "prompt": prompt,
        "description": description,
        "tokens_used": tokens_used,
        "created_at": datetime.utcnow(),
    }

    result = await db.ai_generation_history.insert_one(document)
    logger.info(f"Saved generation history for product {product_id}")
    return str(result.inserted_id)


async def get_generation_history(product_id: int) -> list[dict[str, Any]]:
    """
    Get AI generation history for a product.

    Args:
        product_id: ID of the product

    Returns:
        List of generation history documents
    """
    db = await get_mongodb()

    cursor = db.ai_generation_history.find(
        {"product_id": product_id}
    ).sort("created_at", -1)

    return await cursor.to_list(length=100)


async def get_latest_generation(product_id: int) -> dict[str, Any] | None:
    """
    Get the latest AI generation for a product.

    Args:
        product_id: ID of the product

    Returns:
        Latest generation document or None
    """
    db = await get_mongodb()

    return await db.ai_generation_history.find_one(
        {"product_id": product_id},
        sort=[("created_at", -1)]
    )
