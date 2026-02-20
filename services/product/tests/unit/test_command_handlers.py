"""Unit tests for product command handlers."""

from decimal import Decimal

import pytest
from unittest.mock import AsyncMock

from app.application.commands.product_commands import (
    CreateProductCommand,
    DeleteProductCommand,
    GenerateDescriptionCommand,
)
from app.application.handlers.command_handlers import (
    CreateProductCommandHandler,
    DeleteProductCommandHandler,
    GenerateDescriptionCommandHandler,
)
from app.domain.entities.product import Product
from app.domain.exceptions import ProductAlreadyExistsError, ProductNotFoundError


@pytest.mark.asyncio
async def test_create_product_success(
    mock_uow, mock_llm_service, mock_event_publisher,
    mock_product_cache, mock_history_repo,
):
    created = Product(id=1, name="Test Product", price=Decimal("99.99"), sku="TEST-001")
    mock_uow.products.create = AsyncMock(return_value=created)

    handler = CreateProductCommandHandler(
        mock_uow, mock_event_publisher, mock_product_cache,
        mock_llm_service, mock_history_repo,
    )

    command = CreateProductCommand(
        name="Test Product", price=Decimal("99.99"), sku="TEST-001",
    )
    result = await handler.handle(command)

    assert result.id == 1
    mock_uow.products.create.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_with_ai_description(
    mock_uow, mock_llm_service, mock_event_publisher,
    mock_product_cache, mock_history_repo,
):
    created = Product(
        id=1, name="Test Product", price=Decimal("99.99"), sku="TEST-001",
        description="An excellent product designed for your needs.",
    )
    mock_uow.products.create = AsyncMock(return_value=created)

    handler = CreateProductCommandHandler(
        mock_uow, mock_event_publisher, mock_product_cache,
        mock_llm_service, mock_history_repo,
    )

    command = CreateProductCommand(
        name="Test Product", price=Decimal("99.99"), sku="TEST-001",
        generate_description=True,
    )
    result = await handler.handle(command)

    mock_llm_service.generate_description.assert_called_once()
    mock_history_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_duplicate_sku(
    mock_uow, mock_llm_service, mock_event_publisher,
    mock_product_cache, mock_history_repo,
):
    mock_uow.products.get_by_sku = AsyncMock(
        return_value=Product(id=1, sku="TEST-001")
    )

    handler = CreateProductCommandHandler(
        mock_uow, mock_event_publisher, mock_product_cache,
        mock_llm_service, mock_history_repo,
    )

    command = CreateProductCommand(
        name="Test Product", price=Decimal("99.99"), sku="TEST-001",
    )

    with pytest.raises(ProductAlreadyExistsError):
        await handler.handle(command)


@pytest.mark.asyncio
async def test_delete_product_not_found(
    mock_uow, mock_event_publisher, mock_product_cache,
):
    handler = DeleteProductCommandHandler(mock_uow, mock_event_publisher, mock_product_cache)

    with pytest.raises(ProductNotFoundError):
        await handler.handle(DeleteProductCommand(product_id=999))


@pytest.mark.asyncio
async def test_generate_description(mock_llm_service, mock_history_repo):
    handler = GenerateDescriptionCommandHandler(mock_llm_service, mock_history_repo)

    command = GenerateDescriptionCommand(product_name="Test Product", category="Electronics")
    result = await handler.handle(command)

    assert result == "An excellent product designed for your needs."
    mock_llm_service.generate_description.assert_called_once_with(
        product_name="Test Product", category="Electronics",
    )
