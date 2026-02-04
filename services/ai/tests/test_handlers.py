"""Tests for AI Service event handlers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_handle_product_created_generates_description(
    sample_product_created_event,
    mock_llm_client,
):
    """Test that handler generates description for product without one."""
    with patch("app.handlers.publish_ai_event", new_callable=AsyncMock) as mock_publish, \
         patch("app.handlers.get_cached_description", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.handlers.cache_description", new_callable=AsyncMock) as mock_cache_set, \
         patch("app.handlers.save_generation_history", new_callable=AsyncMock) as mock_save, \
         patch("app.handlers.llm_client", mock_llm_client):

        mock_cache_get.return_value = None
        mock_cache_set.return_value = True

        from app.handlers import handle_product_created
        await handle_product_created(sample_product_created_event)

        # Verify LLM was called
        mock_llm_client.generate.assert_called_once()

        # Verify description was cached
        mock_cache_set.assert_called_once()

        # Verify history was saved
        mock_save.assert_called_once()

        # Verify event was published
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][0] == "description.generated"
        assert call_args[0][1]["product_id"] == 1


@pytest.mark.asyncio
async def test_handle_product_created_skips_with_description(
    sample_product_with_description_event,
    mock_llm_client,
):
    """Test that handler skips products that already have descriptions."""
    with patch("app.handlers.publish_ai_event", new_callable=AsyncMock) as mock_publish, \
         patch("app.handlers.llm_client", mock_llm_client):

        from app.handlers import handle_product_created
        await handle_product_created(sample_product_with_description_event)

        # Verify LLM was not called
        mock_llm_client.generate.assert_not_called()

        # Verify no event was published
        mock_publish.assert_not_called()


@pytest.mark.asyncio
async def test_handle_product_created_uses_cache(
    sample_product_created_event,
    mock_llm_client,
):
    """Test that handler uses cached description if available."""
    cached_description = "Cached product description"

    with patch("app.handlers.publish_ai_event", new_callable=AsyncMock) as mock_publish, \
         patch("app.handlers.get_cached_description", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.handlers.llm_client", mock_llm_client):

        mock_cache_get.return_value = cached_description

        from app.handlers import handle_product_created
        await handle_product_created(sample_product_created_event)

        # Verify cache was checked
        mock_cache_get.assert_called_once_with(1)

        # Verify LLM was not called (using cache)
        mock_llm_client.generate.assert_not_called()

        # Verify event was published with cached description
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][1]["description"] == cached_description
        assert call_args[0][1]["cached"] is True


@pytest.mark.asyncio
async def test_handle_product_created_invalid_data():
    """Test handler handles invalid event data gracefully."""
    invalid_event = {"event_type": "product.created", "data": {}}

    with patch("app.handlers.publish_ai_event", new_callable=AsyncMock) as mock_publish:
        from app.handlers import handle_product_created
        await handle_product_created(invalid_event)

        # Should not publish if data is invalid
        mock_publish.assert_not_called()
