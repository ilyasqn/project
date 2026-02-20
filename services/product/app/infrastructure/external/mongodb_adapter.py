"""MongoDB adapter for generation history - implements GenerationHistoryRepository."""

import logging
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from ...domain.entities.generation_record import GenerationRecord
from ...domain.ports.services import GenerationHistoryRepository

logger = logging.getLogger(__name__)


class MongoGenerationHistoryRepository(GenerationHistoryRepository):
    def __init__(self, database: AsyncIOMotorDatabase):
        self._db = database
        self._collection = database.ai_generation_history

    async def save(self, record: GenerationRecord) -> str:
        document = {
            "product_id": record.product_id,
            "product_name": record.product_name,
            "prompt": record.prompt,
            "description": record.description,
            "tokens_used": record.tokens_used,
            "created_at": datetime.utcnow(),
        }
        result = await self._collection.insert_one(document)
        logger.info(f"Saved generation history for product {record.product_id}")
        return str(result.inserted_id)

    async def get_by_product_id(self, product_id: int) -> list[GenerationRecord]:
        cursor = self._collection.find(
            {"product_id": product_id}
        ).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [
            GenerationRecord(
                id=str(doc["_id"]),
                product_id=doc["product_id"],
                product_name=doc["product_name"],
                prompt=doc["prompt"],
                description=doc["description"],
                tokens_used=doc.get("tokens_used"),
                created_at=doc.get("created_at", datetime.utcnow()),
            )
            for doc in docs
        ]

