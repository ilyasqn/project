"""Tests for AI Service RabbitMQ consumer."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_process_event_dispatches_to_handler():
    """Test that process_event dispatches to correct handler."""
    event_data = {
        "event_type": "product.created",
        "data": {"id": 1, "name": "Test"},
    }

    mock_handler = AsyncMock()

    with patch.dict("app.consumer.EVENT_HANDLERS", {"product.created": mock_handler}):
        from app.consumer import process_event
        await process_event(event_data)
        mock_handler.assert_called_once_with(event_data)


@pytest.mark.asyncio
async def test_process_event_handles_unknown_event():
    """Test that process_event handles unknown event types gracefully."""
    event_data = {
        "event_type": "unknown.event",
        "data": {"id": 1},
    }

    with patch.dict("app.consumer.EVENT_HANDLERS", {}, clear=True):
        from app.consumer import process_event
        # Should not raise exception
        await process_event(event_data)


@pytest.mark.asyncio
async def test_process_event_handles_missing_event_type():
    """Test that process_event handles missing event_type gracefully."""
    event_data = {"data": {"id": 1}}

    from app.consumer import process_event
    # Should not raise exception
    await process_event(event_data)


@pytest.mark.asyncio
async def test_process_event_handles_handler_exception():
    """Test that process_event handles handler exceptions gracefully."""
    event_data = {
        "event_type": "product.created",
        "data": {"id": 1},
    }

    mock_handler = AsyncMock(side_effect=Exception("Test error"))

    with patch.dict("app.consumer.EVENT_HANDLERS", {"product.created": mock_handler}):
        from app.consumer import process_event
        # Should not raise exception
        await process_event(event_data)
        mock_handler.assert_called_once()
