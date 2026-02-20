"""MongoDB adapter for notification logging.

Implements NotificationLogRepository using Motor (async MongoDB driver).
Stores all notification events (email/telegram sends) with timestamps,
enabling audit trails and delivery statistics.
"""

import logging
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ...domain.ports.services import NotificationLogRepository

logger = logging.getLogger(__name__)


class MongoNotificationLogRepository(NotificationLogRepository):
    """Stores and queries notification delivery logs in MongoDB.

    Each log entry records: event_type, delivery channel (email/telegram),
    delivery status (sent/failed), event payload, and timestamp.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        self._db = database
        self._client: AsyncIOMotorClient = database.client
        self._collection = database.notification_logs

    async def log(
        self,
        event_type: str,
        channel: str,
        status: str,
        data: dict[str, Any],
        error: str | None = None,
    ) -> str:
        document = {
            "event_type": event_type,
            "channel": channel,
            "status": status,
            "data": data,
            "error": error,
            "timestamp": datetime.utcnow(),
        }
        result = await self._collection.insert_one(document)
        logger.info(f"Logged notification: {event_type} via {channel} - {status}")
        return str(result.inserted_id)

    async def get_logs(
        self,
        event_type: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query: dict[str, str] = {}
        if event_type:
            query["event_type"] = event_type
        if channel:
            query["channel"] = channel
        if status:
            query["status"] = status

        cursor = self._collection.find(query).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_stats(self) -> dict[str, Any]:
        pipeline = [
            {
                "$group": {
                    "_id": {"channel": "$channel", "status": "$status"},
                    "count": {"$sum": 1},
                }
            }
        ]
        cursor = self._db.notification_logs.aggregate(pipeline)
        results = await cursor.to_list(length=100)

        stats: dict[str, dict[str, int]] = {}
        for result in results:
            channel = result["_id"]["channel"]
            status = result["_id"]["status"]
            count = result["count"]
            if channel not in stats:
                stats[channel] = {}
            stats[channel][status] = count
        return stats

    async def close(self) -> None:
        self._client.close()
        logger.info("MongoDB notification log connection closed")
