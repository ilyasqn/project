"""Pytest fixtures for Notification Service tests."""

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
def mock_telegram_service():
    """Mock Telegram service."""
    with patch("app.telegram.telegram_service") as mock:
        mock.enabled = True
        mock.send_event_notification = AsyncMock(return_value=True)
        mock.send_message = AsyncMock(return_value=True)
        mock.close = AsyncMock()
        yield mock


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client."""
    with patch("app.mongodb.get_mongodb") as mock:
        db = AsyncMock()
        db.notification_logs = AsyncMock()
        db.notification_logs.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id="test_id")
        )
        db.notification_logs.find = MagicMock(
            return_value=MagicMock(
                sort=MagicMock(
                    return_value=MagicMock(
                        limit=MagicMock(
                            return_value=AsyncMock(to_list=AsyncMock(return_value=[]))
                        )
                    )
                )
            )
        )
        mock.return_value = db
        yield db


@pytest.fixture
def sample_user_created_event():
    """Sample user.created event data."""
    return {
        "event_type": "user.created",
        "data": {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_active": True,
        },
    }


@pytest.fixture
def sample_product_created_event():
    """Sample product.created event data."""
    return {
        "event_type": "product.created",
        "data": {
            "id": 1,
            "name": "Test Product",
            "price": "99.99",
            "sku": "TEST-001",
            "category": "Electronics",
        },
    }


@pytest.fixture
def sample_ai_description_event():
    """Sample ai.description.generated event data."""
    return {
        "event_type": "ai.description.generated",
        "data": {
            "product_id": 1,
            "description": "An excellent product.",
            "cached": False,
        },
    }
