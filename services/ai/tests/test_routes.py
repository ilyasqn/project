"""Tests for AI Service API routes."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies for route tests."""
    with patch("app.consumer.start_consuming", new_callable=AsyncMock), \
         patch("app.consumer.close_consumer", new_callable=AsyncMock), \
         patch("app.events.close_publisher", new_callable=AsyncMock), \
         patch("app.mongodb.close_mongodb", new_callable=AsyncMock), \
         patch("app.redis_cache.close_redis", new_callable=AsyncMock), \
         patch("app.events.get_publisher") as mock_pub:
        publisher = AsyncMock()
        publisher.publish = AsyncMock()
        mock_pub.return_value = publisher
        yield


@pytest.fixture
async def client(mock_dependencies):
    """Create test client."""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai"


@pytest.mark.asyncio
async def test_generate_endpoint(client):
    """Test AI generation endpoint."""
    with patch("app.routes.llm_client") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="Generated text")
        mock_llm.model = "gpt-3.5-turbo"

        response = await client.post(
            "/ai/generate",
            json={
                "prompt": "Generate a product description",
                "max_tokens": 100,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "text" in data


@pytest.mark.asyncio
async def test_summarize_endpoint(client):
    """Test AI summarize endpoint."""
    with patch("app.routes.llm_client") as mock_llm:
        mock_llm.summarize = AsyncMock(return_value="Summary text")

        response = await client.post(
            "/ai/summarize",
            json={
                "text": "This is a long text that needs to be summarized.",
                "max_length": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data


@pytest.mark.asyncio
async def test_analyze_endpoint(client):
    """Test AI analyze endpoint."""
    with patch("app.routes.llm_client") as mock_llm:
        mock_llm.analyze = AsyncMock(return_value={"sentiment": "positive"})

        response = await client.post(
            "/ai/analyze",
            json={
                "text": "I love this product!",
                "analysis_type": "sentiment",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "analysis_type" in data
