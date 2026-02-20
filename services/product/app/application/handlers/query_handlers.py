"""Product query handlers (read-only operations)."""

import logging
from decimal import Decimal

from ...domain.entities.generation_record import GenerationRecord
from ...domain.entities.product import Product
from ...domain.exceptions import ProductNotFoundError
from ...domain.ports.services import GenerationHistoryRepository
from ...infrastructure.cache.redis_adapter import RedisProductCache
from ...infrastructure.persistence.uow import UnitOfWork
from ..queries.product_queries import GetGenerationHistoryQuery, GetProductQuery, ListProductsQuery

logger = logging.getLogger(__name__)


class GetProductQueryHandler:
    def __init__(self, uow: UnitOfWork, cache: RedisProductCache):
        self._uow = uow
        self._cache = cache

    async def handle(self, query: GetProductQuery) -> Product:
        cached = await self._cache.get(query.product_id)
        if cached:
            logger.info(f"Cache hit for product {query.product_id}")
            cached["price"] = Decimal(cached["price"])
            return Product(**cached)

        async with self._uow:
            product = await self._uow.products.get_by_id(query.product_id)
            if not product:
                raise ProductNotFoundError(f"Product {query.product_id} not found")

        await self._cache.set(query.product_id, product.to_dict())
        return product


class ListProductsQueryHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: ListProductsQuery) -> tuple[list[Product], int]:
        async with self._uow:
            products = await self._uow.products.list_products(
                skip=query.skip, limit=query.limit, category=query.category,
            )
            total = await self._uow.products.count(category=query.category)
        return products, total


class GetGenerationHistoryQueryHandler:
    def __init__(self, history: GenerationHistoryRepository):
        self._history = history

    async def handle(self, query: GetGenerationHistoryQuery) -> list[GenerationRecord]:
        return await self._history.get_by_product_id(query.product_id)
