"""Integration tests for the microservices system (Clean Architecture)."""

from decimal import Decimal

import pytest
from unittest.mock import AsyncMock

from services.user.app.application.commands.user_commands import CreateUserCommand
from services.user.app.application.handlers.command_handlers import CreateUserCommandHandler
from services.user.app.domain.entities.user import User

from services.product.app.application.commands.product_commands import CreateProductCommand
from services.product.app.application.handlers.command_handlers import CreateProductCommandHandler
from services.product.app.domain.entities.product import Product

from services.notification.app.application.handlers.event_handlers import (
    UserCreatedEventHandler,
    ProductCreatedEventHandler,
)


@pytest.mark.asyncio
async def test_full_flow_create_user_to_notification(
    mock_user_uow, mock_user_repository, mock_event_publisher, mock_cache,
    mock_email_service, mock_telegram_service, mock_log_repo,
):
    """Test: Create user -> event published -> notification handler processes it."""
    created_user = User(id=1, email="test@example.com", username="testuser", full_name="Test User")
    mock_user_repository.create = AsyncMock(return_value=created_user)

    handler = CreateUserCommandHandler(mock_user_uow, mock_event_publisher, mock_cache)
    user = await handler.handle(CreateUserCommand(
        email="test@example.com", username="testuser",
        full_name="Test User", password="password123",
    ))

    assert user.id == 1
    mock_event_publisher.publish.assert_called_once()

    event_data = mock_event_publisher.publish.call_args[0][1]
    notification_handler = UserCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )
    await notification_handler.handle(event_data)

    mock_email_service.send_welcome_email.assert_called_once()
    mock_telegram_service.send_event_notification.assert_called_once()
    assert mock_log_repo.log.call_count == 2


@pytest.mark.asyncio
async def test_full_flow_create_product_with_llm_description(
    mock_product_uow, mock_product_repository, mock_llm_service, mock_event_publisher,
    mock_cache, mock_history_repo,
    mock_email_service, mock_telegram_service, mock_log_repo,
):
    """Test: Create product with generate_description -> LLM called internally -> notification sent."""
    created_product = Product(
        id=1, name="Test Product", price=Decimal("99.99"), sku="TEST-001",
        description="An excellent product designed for your needs.",
    )
    mock_product_repository.create = AsyncMock(return_value=created_product)

    handler = CreateProductCommandHandler(mock_product_uow, mock_event_publisher, mock_cache, mock_llm_service, mock_history_repo)
    product = await handler.handle(CreateProductCommand(
        name="Test Product", price=Decimal("99.99"), sku="TEST-001",
        category="Electronics", generate_description=True,
    ))

    mock_llm_service.generate_description.assert_called_once()
    mock_history_repo.save.assert_called_once()
    mock_event_publisher.publish.assert_called_once()

    event_data = mock_event_publisher.publish.call_args[0][1]
    notification_handler = ProductCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )
    await notification_handler.handle(event_data)

    mock_email_service.send_new_product_notification.assert_called_once()
    mock_telegram_service.send_event_notification.assert_called_once()


@pytest.mark.asyncio
async def test_notification_service_handles_all_event_types(
    mock_email_service, mock_telegram_service, mock_log_repo,
):
    """Test that notification service handles user.* and product.* events (no ai.* events)."""
    from services.notification.app.application.handlers.event_handlers import (
        UserCreatedEventHandler,
        ProductCreatedEventHandler,
        ProductDeletedEventHandler,
    )

    user_handler = UserCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )
    await user_handler.handle({
        "event_type": "user.created",
        "data": {"id": 1, "email": "test@example.com", "full_name": "Test"},
    })
    mock_email_service.send_welcome_email.assert_called_once()

    product_handler = ProductCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )
    await product_handler.handle({
        "event_type": "product.created",
        "data": {"id": 1, "name": "Product", "price": "99.99"},
    })
    mock_email_service.send_new_product_notification.assert_called_once()

    delete_handler = ProductDeletedEventHandler(
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )
    await delete_handler.handle({
        "event_type": "product.deleted",
        "data": {"id": 1, "name": "Product"},
    })

    assert mock_telegram_service.send_event_notification.call_count == 3


@pytest.mark.asyncio
async def test_mongodb_logging_for_notifications(
    mock_email_service, mock_telegram_service, mock_log_repo,
):
    """Test that all notifications are logged to MongoDB."""
    handler = UserCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )

    await handler.handle({
        "event_type": "user.created",
        "data": {"id": 1, "email": "test@example.com"},
    })

    assert mock_log_repo.log.call_count == 2
    log_calls = mock_log_repo.log.call_args_list

    assert log_calls[0][0][1] == "email"
    assert log_calls[0][0][2] == "sent"

    assert log_calls[1][0][1] == "telegram"
    assert log_calls[1][0][2] == "sent"


@pytest.mark.asyncio
async def test_no_circular_dependency_product_creates_description_internally(
    mock_product_uow, mock_product_repository, mock_llm_service, mock_event_publisher,
    mock_cache, mock_history_repo,
):
    """
    Verify there is no circular event dependency.
    Product service generates descriptions internally via LLM port,
    not through an external AI service event loop.
    """
    created_product = Product(
        id=1, name="Test Product", price=Decimal("99.99"), sku="TEST-001",
        description="Generated description",
    )
    mock_product_repository.create = AsyncMock(return_value=created_product)

    handler = CreateProductCommandHandler(mock_product_uow, mock_event_publisher, mock_cache, mock_llm_service, mock_history_repo)
    product = await handler.handle(CreateProductCommand(
        name="Test Product", price=Decimal("99.99"), sku="TEST-001",
        generate_description=True,
    ))

    mock_llm_service.generate_description.assert_called_once()

    assert mock_event_publisher.publish.call_count == 1
    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event == "product.created"
