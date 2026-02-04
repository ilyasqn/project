"""MongoDB client for Notification Service logs."""

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


async def log_notification(
    event_type: str,
    channel: str,
    status: str,
    data: dict[str, Any],
    error: str | None = None,
) -> str:
    """
    Log a notification to MongoDB.

    Args:
        event_type: Type of the event that triggered the notification
        channel: Notification channel (email, telegram, sms, push)
        status: Delivery status (sent, failed)
        data: The notification data/payload
        error: Error message if failed

    Returns:
        ID of the inserted document
    """
    db = await get_mongodb()

    document = {
        "event_type": event_type,
        "channel": channel,
        "status": status,
        "data": data,
        "error": error,
        "timestamp": datetime.utcnow(),
    }

    result = await db.notification_logs.insert_one(document)
    logger.info(f"Logged notification: {event_type} via {channel} - {status}")
    return str(result.inserted_id)


async def get_notification_logs(
    event_type: str | None = None,
    channel: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Get notification logs from MongoDB.

    Args:
        event_type: Filter by event type (optional)
        channel: Filter by channel (optional)
        status: Filter by status (optional)
        limit: Maximum number of results

    Returns:
        List of notification log documents
    """
    db = await get_mongodb()

    query = {}
    if event_type:
        query["event_type"] = event_type
    if channel:
        query["channel"] = channel
    if status:
        query["status"] = status

    cursor = db.notification_logs.find(query).sort("timestamp", -1).limit(limit)

    return await cursor.to_list(length=limit)


async def get_notification_stats() -> dict[str, Any]:
    """
    Get notification statistics.

    Returns:
        Dictionary with notification statistics
    """
    db = await get_mongodb()

    pipeline = [
        {
            "$group": {
                "_id": {
                    "channel": "$channel",
                    "status": "$status",
                },
                "count": {"$sum": 1},
            }
        }
    ]

    cursor = db.notification_logs.aggregate(pipeline)
    results = await cursor.to_list(length=100)

    stats = {}
    for result in results:
        channel = result["_id"]["channel"]
        status = result["_id"]["status"]
        count = result["count"]

        if channel not in stats:
            stats[channel] = {}
        stats[channel][status] = count

    return stats
