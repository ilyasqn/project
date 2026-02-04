"""Tests for Telegram notification service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_telegram_service_disabled_without_config():
    """Test that Telegram service is disabled without configuration."""
    with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
        # Re-import to get fresh instance
        from importlib import reload
        import app.telegram
        reload(app.telegram)

        assert app.telegram.telegram_service.enabled is False


@pytest.mark.asyncio
async def test_telegram_send_message_disabled():
    """Test that send_message returns False when disabled."""
    with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
        from importlib import reload
        import app.telegram
        reload(app.telegram)

        result = await app.telegram.telegram_service.send_message("Test message")
        assert result is False


@pytest.mark.asyncio
async def test_format_event_message_user_created():
    """Test message formatting for user.created event."""
    with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
        from importlib import reload
        import app.telegram
        reload(app.telegram)

        service = app.telegram.TelegramService()

        data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
        }

        message = service._format_event_message("user.created", data)

        # Check emoji is present
        assert "\U0001F464" in message  # person silhouette emoji

        # Check event type is in header
        assert "USER.CREATED" in message

        # Check data fields are present
        assert "id:" in message
        assert "email:" in message
        assert "testuser" in message


@pytest.mark.asyncio
async def test_format_event_message_truncates_long_values():
    """Test that long values are truncated in messages."""
    with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
        from importlib import reload
        import app.telegram
        reload(app.telegram)

        service = app.telegram.TelegramService()

        long_value = "x" * 200
        data = {"description": long_value}

        message = service._format_event_message("test.event", data)

        # Check value is truncated
        assert "..." in message
        assert len(message) < len(long_value) + 100


@pytest.mark.asyncio
async def test_telegram_send_event_notification_enabled():
    """Test send_event_notification when Telegram is enabled."""
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    with patch("app.telegram.TELEGRAM_BOT_TOKEN", "test_token"), \
         patch("app.telegram.TELEGRAM_CHAT_ID", "123456"), \
         patch("app.telegram.Bot", return_value=mock_bot):

        from app.telegram import TelegramService

        service = TelegramService()
        service.bot = mock_bot
        service._enabled = True

        result = await service.send_event_notification(
            "user.created",
            {"id": 1, "email": "test@example.com"},
        )

        assert result is True
        mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_telegram_handles_api_error():
    """Test that Telegram service handles API errors gracefully."""
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock(side_effect=Exception("API Error"))

    with patch("app.telegram.Bot", return_value=mock_bot), \
         patch("app.telegram.TELEGRAM_BOT_TOKEN", "123456:ABC-DEF"), \
         patch("app.telegram.TELEGRAM_CHAT_ID", "123456"):

        from importlib import reload
        import app.telegram
        reload(app.telegram)

        service = app.telegram.TelegramService()
        service.bot = mock_bot
        service._enabled = True

        result = await service.send_message("Test message")

        assert result is False
