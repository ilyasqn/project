"""Pytest fixtures for Product Service tests."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add paths for imports
sys.path.insert(0, "/app")


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ client."""
    with patch("shared.rabbitmq.RabbitMQClient") as mock:
        client = AsyncMock()
        client.connect = AsyncMock()
        client.close = AsyncMock()
        client.publish = AsyncMock()
        client.subscribe = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("app.redis_cache.get_redis") as mock:
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        mock.return_value = client
        yield client


@pytest.fixture
def mock_database():
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_product():
    """Sample product data."""
    return {
        "id": 1,
        "name": "Test Product",
        "description": None,
        "price": "99.99",
        "sku": "TEST-001",
        "stock_quantity": 10,
        "category": "Electronics",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_description_generated_event():
    """Sample ai.description.generated event data."""
    return {
        "event_type": "ai.description.generated",
        "data": {
            "product_id": 1,
            "description": "A fantastic product with excellent features.",
            "cached": False,
        },
    }
