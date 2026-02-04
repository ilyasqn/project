"""Tests for Product Service event handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_handle_description_generated_updates_product(
    sample_description_generated_event,
):
    """Test that handler updates product with AI-generated description."""
    mock_product = MagicMock()
    mock_product.description = None
    mock_product.to_dict.return_value = {
        "id": 1,
        "name": "Test",
        "description": "A fantastic product with excellent features.",
    }

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_product

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    with patch("app.handlers.async_session_maker") as mock_session_maker, \
         patch("app.handlers.invalidate_product_cache", new_callable=AsyncMock) as mock_invalidate, \
         patch("app.handlers.publish_product_event", new_callable=AsyncMock) as mock_publish:

        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        from app.handlers import handle_description_generated

        await handle_description_generated(sample_description_generated_event)

        # Verify product was updated
        assert mock_product.description == "A fantastic product with excellent features."

        # Verify session was committed
        mock_session.commit.assert_called_once()

        # Verify cache was invalidated
        mock_invalidate.assert_called_once_with(1)

        # Verify product.updated event was published
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][0] == "updated"


@pytest.mark.asyncio
async def test_handle_description_generated_skips_existing_description(
    sample_description_generated_event,
):
    """Test that handler skips if product already has description."""
    mock_product = MagicMock()
    mock_product.description = "Existing description"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_product

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.handlers.async_session_maker") as mock_session_maker, \
         patch("app.handlers.publish_product_event", new_callable=AsyncMock) as mock_publish:

        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        from app.handlers import handle_description_generated

        await handle_description_generated(sample_description_generated_event)

        # Verify no commit was made
        mock_session.commit.assert_not_called()

        # Verify no event was published
        mock_publish.assert_not_called()


@pytest.mark.asyncio
async def test_handle_description_generated_product_not_found(
    sample_description_generated_event,
):
    """Test handler handles non-existent product gracefully."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.handlers.async_session_maker") as mock_session_maker, \
         patch("app.handlers.publish_product_event", new_callable=AsyncMock) as mock_publish:

        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock()

        from app.handlers import handle_description_generated

        await handle_description_generated(sample_description_generated_event)

        # Verify no event was published
        mock_publish.assert_not_called()


@pytest.mark.asyncio
async def test_handle_description_generated_invalid_data():
    """Test handler handles invalid event data gracefully."""
    invalid_event = {"event_type": "ai.description.generated", "data": {}}

    with patch("app.handlers.async_session_maker") as mock_session_maker:
        from app.handlers import handle_description_generated

        # Should not raise exception and should not create session
        await handle_description_generated(invalid_event)

        mock_session_maker.assert_not_called()
