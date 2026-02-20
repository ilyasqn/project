"""Unit tests for notification event handlers."""

import pytest

from app.application.handlers.event_handlers import (
    UserCreatedEventHandler,
    UserUpdatedEventHandler,
    ProductCreatedEventHandler,
    ProductDeletedEventHandler,
)


@pytest.mark.asyncio
async def test_user_created_handler(mock_email_service, mock_telegram_service, mock_log_repo):
    handler = UserCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )

    event = {
        "event_type": "user.created",
        "data": {"id": 1, "email": "test@example.com", "full_name": "Test User"},
    }
    await handler.handle(event)

    mock_email_service.send_welcome_email.assert_called_once()
    mock_telegram_service.send_event_notification.assert_called_once_with(
        "user.created", event["data"]
    )
    assert mock_log_repo.log.call_count == 2


@pytest.mark.asyncio
async def test_user_updated_handler(mock_email_service, mock_telegram_service, mock_log_repo):
    handler = UserUpdatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )

    event = {
        "event_type": "user.updated",
        "data": {"id": 1, "email": "test@example.com"},
    }
    await handler.handle(event)

    mock_email_service.send_user_update_notification.assert_called_once()
    mock_telegram_service.send_event_notification.assert_called_once()
    assert mock_log_repo.log.call_count == 2


@pytest.mark.asyncio
async def test_product_created_handler(mock_email_service, mock_telegram_service, mock_log_repo):
    handler = ProductCreatedEventHandler(
        email_service=mock_email_service,
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )

    event = {
        "event_type": "product.created",
        "data": {"id": 1, "name": "Test Product", "price": "99.99"},
    }
    await handler.handle(event)

    mock_email_service.send_new_product_notification.assert_called_once()
    mock_telegram_service.send_event_notification.assert_called_once()


@pytest.mark.asyncio
async def test_product_deleted_handler(mock_telegram_service, mock_log_repo):
    handler = ProductDeletedEventHandler(
        telegram_service=mock_telegram_service,
        log_repo=mock_log_repo,
    )

    event = {
        "event_type": "product.deleted",
        "data": {"id": 1, "name": "Test Product"},
    }
    await handler.handle(event)

    mock_telegram_service.send_event_notification.assert_called_once()
    mock_log_repo.log.assert_called_once()
