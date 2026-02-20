"""Product command handlers.

Each handler does one use case:
  1. Open UoW transaction
  2. Run business logic
  3. Commit
  4. Publish events (after commit for consistency)
"""

import logging

from ...domain.entities.generation_record import GenerationRecord
from ...domain.entities.product import Product
from ...domain.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from ...domain.ports.services import GenerationHistoryRepository, LLMService
from ...infrastructure.cache.redis_adapter import RedisProductCache
from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQProductEventPublisher
from ...infrastructure.persistence.uow import UnitOfWork
from ..commands.product_commands import (
    CreateProductCommand,
    DeleteProductCommand,
    GenerateDescriptionCommand,
    UpdateProductCommand,
)

logger = logging.getLogger(__name__)


class CreateProductCommandHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        events: RabbitMQProductEventPublisher,
        cache: RedisProductCache,
        llm: LLMService,
        history: GenerationHistoryRepository,
    ):
        self._uow = uow
        self._events = events
        self._cache = cache
        self._llm = llm
        self._history = history

    async def handle(self, command: CreateProductCommand) -> Product:
        async with self._uow:
            await self._check_unique_sku(command.sku)
            description = await self._resolve_description(command)
            product = self._build_product(command, description)
            product = await self._uow.products.create(product)
            await self._uow.commit()

        if command.generate_description and description:
            await self._save_generation_history(product, command, description)

        await self._events.publish(
            "product.created",
            {"event_type": "product.created", "data": product.to_dict()},
        )
        logger.info(f"Created product {product.id}")
        return product

    async def _check_unique_sku(self, sku: str) -> None:
        if await self._uow.products.get_by_sku(sku):
            raise ProductAlreadyExistsError("Product with this SKU already exists")

    async def _resolve_description(self, command: CreateProductCommand) -> str | None:
        if command.generate_description and not command.description:
            return await self._llm.generate_description(
                product_name=command.name,
                category=command.category,
                price=str(command.price),
            )
        return command.description

    def _build_product(self, command: CreateProductCommand, description: str | None) -> Product:
        return Product(
            name=command.name,
            description=description,
            price=command.price,
            sku=command.sku,
            stock_quantity=command.stock_quantity,
            category=command.category,
        )

    async def _save_generation_history(
        self, product: Product, command: CreateProductCommand, description: str,
    ) -> None:
        prompt = f"Generate description for: {command.name}"
        if command.category:
            prompt += f", category: {command.category}"
        record = GenerationRecord(
            product_id=product.id,
            product_name=product.name,
            prompt=prompt,
            description=description,
        )
        await self._history.save(record)


class UpdateProductCommandHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        events: RabbitMQProductEventPublisher,
        cache: RedisProductCache,
    ):
        self._uow = uow
        self._events = events
        self._cache = cache

    async def handle(self, command: UpdateProductCommand) -> Product:
        async with self._uow:
            product = await self._uow.products.get_by_id(command.product_id)
            if not product:
                raise ProductNotFoundError(f"Product {command.product_id} not found")

            self._apply_changes(product, command)
            product = await self._uow.products.update(product)
            await self._uow.commit()

        await self._cache.delete(command.product_id)
        await self._events.publish(
            "product.updated",
            {"event_type": "product.updated", "data": product.to_dict()},
        )
        logger.info(f"Updated product {product.id}")
        return product

    def _apply_changes(self, product: Product, command: UpdateProductCommand) -> None:
        for field in ("name", "description", "price", "stock_quantity", "category", "is_active"):
            value = getattr(command, field)
            if value is not None:
                setattr(product, field, value)


class DeleteProductCommandHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        events: RabbitMQProductEventPublisher,
        cache: RedisProductCache,
    ):
        self._uow = uow
        self._events = events
        self._cache = cache

    async def handle(self, command: DeleteProductCommand) -> None:
        async with self._uow:
            product = await self._uow.products.get_by_id(command.product_id)
            if not product:
                raise ProductNotFoundError(f"Product {command.product_id} not found")

            product_data = product.to_dict()
            await self._uow.products.delete(command.product_id)
            await self._uow.commit()

        await self._cache.delete(command.product_id)
        await self._events.publish(
            "product.deleted",
            {"event_type": "product.deleted", "data": product_data},
        )
        logger.info(f"Deleted product {command.product_id}")


class GenerateDescriptionCommandHandler:
    def __init__(self, llm: LLMService, history: GenerationHistoryRepository):
        self._llm = llm
        self._history = history

    async def handle(self, command: GenerateDescriptionCommand) -> str:
        return await self._llm.generate_description(
            product_name=command.product_name,
            category=command.category,
        )
