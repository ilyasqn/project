"""Tests for Notification Service event handlers."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_handle_user_created_sends_notifications(
    sample_user_created_event,
):
    """Test that user.created handler sends email and Telegram notifications."""
    with patch("app.handlers.email_service") as mock_email, \
         patch("app.handlers.telegram_service") as mock_telegram, \
         patch("app.handlers.log_notification", new_callable=AsyncMock) as mock_log:

        mock_email.send_welcome_email = AsyncMock(return_value=True)
        mock_telegram.send_event_notification = AsyncMock(return_value=True)

        from app.handlers import handle_user_created

        await handle_user_created(sample_user_created_event)

        # Verify email was sent
        mock_email.send_welcome_email.assert_called_once()

        # Verify Telegram notification was sent
        mock_telegram.send_event_notification.assert_called_once_with(
            "user.created",
            sample_user_created_event["data"],
        )

        # Verify both notifications were logged
        assert mock_log.call_count == 2


@pytest.mark.asyncio
async def test_handle_product_created_sends_notifications(
    sample_product_created_event,
):
    """Test that product.created handler sends email and Telegram notifications."""
    with patch("app.handlers.email_service") as mock_email, \
         patch("app.handlers.telegram_service") as mock_telegram, \
         patch("app.handlers.log_notification", new_callable=AsyncMock) as mock_log:

        mock_email.send_new_product_notification = AsyncMock(return_value=True)
        mock_telegram.send_event_notification = AsyncMock(return_value=True)

        from app.handlers import handle_product_created

        await handle_product_created(sample_product_created_event)

        # Verify email was sent
        mock_email.send_new_product_notification.assert_called_once()

        # Verify Telegram notification was sent
        mock_telegram.send_event_notification.assert_called_once()

        # Verify both notifications were logged
        assert mock_log.call_count == 2


@pytest.mark.asyncio
async def test_handle_ai_description_generated_sends_telegram(
    sample_ai_description_event,
):
    """Test that ai.description.generated handler sends Telegram notification."""
    with patch("app.handlers.telegram_service") as mock_telegram, \
         patch("app.handlers.log_notification", new_callable=AsyncMock) as mock_log:

        mock_telegram.send_event_notification = AsyncMock(return_value=True)

        from app.handlers import handle_ai_description_generated

        await handle_ai_description_generated(sample_ai_description_event)

        # Verify Telegram notification was sent
        mock_telegram.send_event_notification.assert_called_once_with(
            "ai.description.generated",
            sample_ai_description_event["data"],
        )

        # Verify notification was logged
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_handler_logs_failed_notifications(sample_user_created_event):
    """Test that failed notifications are logged with 'failed' status."""
    with patch("app.handlers.email_service") as mock_email, \
         patch("app.handlers.telegram_service") as mock_telegram, \
         patch("app.handlers.log_notification", new_callable=AsyncMock) as mock_log:

        mock_email.send_welcome_email = AsyncMock(return_value=False)
        mock_telegram.send_event_notification = AsyncMock(return_value=False)

        from app.handlers import handle_user_created

        await handle_user_created(sample_user_created_event)

        # Verify both failures were logged
        log_calls = mock_log.call_args_list

        # Check email log
        email_call = log_calls[0]
        assert email_call[0][0] == "user.created"
        assert email_call[0][1] == "email"
        assert email_call[0][2] == "failed"

        # Check telegram log
        telegram_call = log_calls[1]
        assert telegram_call[0][0] == "user.created"
        assert telegram_call[0][1] == "telegram"
        assert telegram_call[0][2] == "failed"
