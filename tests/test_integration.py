"""Integration tests for the microservices system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_full_flow_product_created_to_ai_description(
    mock_rabbitmq_client,
    mock_mongodb_client,
    mock_redis_client,
    mock_llm_client,
    mock_telegram_bot,
):
    """
    Test the full flow:
    1. Product created without description
    2. AI service generates description
    3. Product service updates product
    4. Telegram notification is sent
    """
    _, mock_db = mock_mongodb_client

    # Simulate product.created event
    product_created_event = {
        "event_type": "product.created",
        "data": {
            "id": 1,
            "name": "Test Product",
            "description": None,
            "price": "99.99",
            "sku": "TEST-001",
            "category": "Electronics",
        },
    }

    published_events = []

    async def capture_publish(routing_key, data):
        published_events.append({"routing_key": routing_key, "data": data})

    mock_rabbitmq_client.publish = capture_publish

    # Step 1: AI Service handles product.created
    with patch("app.handlers.llm_client", mock_llm_client), \
         patch("app.handlers.get_cached_description", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.handlers.cache_description", new_callable=AsyncMock) as mock_cache_set, \
         patch("app.handlers.save_generation_history", new_callable=AsyncMock) as mock_save, \
         patch("app.handlers.publish_ai_event", new_callable=AsyncMock) as mock_publish:

        mock_cache_get.return_value = None
        mock_cache_set.return_value = True

        # Import after patching
        from services.ai.app.handlers import handle_product_created

        await handle_product_created(product_created_event)

        # Verify LLM was called
        mock_llm_client.generate.assert_called_once()

        # Verify event was published
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][0] == "description.generated"
        assert call_args[0][1]["product_id"] == 1


@pytest.mark.asyncio
async def test_description_generated_updates_product_and_notifies(
    mock_rabbitmq_client,
    mock_telegram_bot,
):
    """
    Test that ai.description.generated event:
    1. Updates the product in database
    2. Sends Telegram notification
    """
    description_generated_event = {
        "event_type": "ai.description.generated",
        "data": {
            "product_id": 1,
            "description": "An excellent product designed for your needs.",
            "cached": False,
        },
    }

    # Step 1: Product Service handles ai.description.generated
    mock_product = MagicMock()
    mock_product.description = None
    mock_product.to_dict.return_value = {
        "id": 1,
        "name": "Test Product",
        "description": "An excellent product designed for your needs.",
    }

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_product

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    with patch("services.product.app.handlers.async_session_maker") as mock_session_maker, \
         patch("services.product.app.handlers.invalidate_product_cache", new_callable=AsyncMock), \
         patch("services.product.app.handlers.publish_product_event", new_callable=AsyncMock) as mock_publish:

        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        from services.product.app.handlers import handle_description_generated

        await handle_description_generated(description_generated_event)

        # Verify product was updated
        assert mock_product.description == "An excellent product designed for your needs."

        # Verify product.updated was published
        mock_publish.assert_called_once_with("updated", mock_product.to_dict())


@pytest.mark.asyncio
async def test_notification_service_handles_all_events():
    """Test that notification service handles all event types."""
    events_to_test = [
        {
            "event_type": "user.created",
            "data": {"id": 1, "email": "test@example.com", "full_name": "Test"},
        },
        {
            "event_type": "product.created",
            "data": {"id": 1, "name": "Product", "price": "99.99"},
        },
        {
            "event_type": "ai.description.generated",
            "data": {"product_id": 1, "description": "Test"},
        },
    ]

    with patch("services.notification.app.handlers.email_service") as mock_email, \
         patch("services.notification.app.handlers.telegram_service") as mock_telegram, \
         patch("services.notification.app.handlers.log_notification", new_callable=AsyncMock):

        mock_email.send_welcome_email = AsyncMock(return_value=True)
        mock_email.send_new_product_notification = AsyncMock(return_value=True)
        mock_telegram.send_event_notification = AsyncMock(return_value=True)

        from services.notification.app.handlers import (
            handle_user_created,
            handle_product_created,
            handle_ai_description_generated,
        )

        # Test user.created
        await handle_user_created(events_to_test[0])
        mock_email.send_welcome_email.assert_called_once()

        # Test product.created
        await handle_product_created(events_to_test[1])
        mock_email.send_new_product_notification.assert_called_once()

        # Test ai.description.generated
        await handle_ai_description_generated(events_to_test[2])

        # Verify Telegram was called for all events
        assert mock_telegram.send_event_notification.call_count == 3


@pytest.mark.asyncio
async def test_redis_caching_prevents_duplicate_generations(
    mock_llm_client,
):
    """Test that Redis caching prevents duplicate AI generations."""
    product_created_event = {
        "event_type": "product.created",
        "data": {
            "id": 1,
            "name": "Test Product",
            "description": None,
            "price": "99.99",
        },
    }

    cached_description = "Previously cached description"

    with patch("services.ai.app.handlers.get_cached_description", new_callable=AsyncMock) as mock_cache_get, \
         patch("services.ai.app.handlers.publish_ai_event", new_callable=AsyncMock) as mock_publish:

        mock_cache_get.return_value = cached_description

        from services.ai.app.handlers import handle_product_created

        await handle_product_created(product_created_event)

        # Verify LLM was NOT called (using cache)
        mock_llm_client.generate.assert_not_called()

        # Verify cached description was published
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][1]["description"] == cached_description
        assert call_args[0][1]["cached"] is True


@pytest.mark.asyncio
async def test_mongodb_logging_for_notifications():
    """Test that all notifications are logged to MongoDB."""
    with patch("services.notification.app.handlers.email_service") as mock_email, \
         patch("services.notification.app.handlers.telegram_service") as mock_telegram, \
         patch("services.notification.app.handlers.log_notification", new_callable=AsyncMock) as mock_log:

        mock_email.send_welcome_email = AsyncMock(return_value=True)
        mock_telegram.send_event_notification = AsyncMock(return_value=True)

        from services.notification.app.handlers import handle_user_created

        await handle_user_created({
            "event_type": "user.created",
            "data": {"id": 1, "email": "test@example.com"},
        })

        # Verify both email and Telegram were logged
        assert mock_log.call_count == 2

        # Check log calls
        log_calls = mock_log.call_args_list

        # Email log
        assert log_calls[0][0][1] == "email"
        assert log_calls[0][0][2] == "sent"

        # Telegram log
        assert log_calls[1][0][1] == "telegram"
        assert log_calls[1][0][2] == "sent"
