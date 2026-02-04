"""Pytest fixtures for Notification Service tests."""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add paths for imports
sys.path.insert(0, "/app")


# =============================================================================
# Sample Data - Users
# =============================================================================

SAMPLE_USERS = [
    {
        "id": 1,
        "email": "john@example.com",
        "username": "johndoe",
        "full_name": "John Doe",
        "is_active": True,
        "created_at": "2024-01-01T10:00:00",
    },
    {
        "id": 2,
        "email": "jane@example.com",
        "username": "janesmith",
        "full_name": "Jane Smith",
        "is_active": True,
        "created_at": "2024-01-02T11:00:00",
    },
    {
        "id": 3,
        "email": "bob@example.com",
        "username": "bobwilson",
        "full_name": "Bob Wilson",
        "is_active": False,
        "created_at": "2024-01-03T12:00:00",
    },
]


# =============================================================================
# Sample Data - Products
# =============================================================================

SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "name": "Wireless Bluetooth Headphones",
        "price": "99.99",
        "sku": "WBH-001",
        "category": "Electronics",
    },
    {
        "id": 2,
        "name": "Mechanical Gaming Keyboard",
        "price": "149.99",
        "sku": "MGK-002",
        "category": "Electronics",
    },
    {
        "id": 3,
        "name": "Ergonomic Office Chair",
        "price": "299.99",
        "sku": "EOC-003",
        "category": "Furniture",
    },
]


# =============================================================================
# Sample Data - Notification Logs (MongoDB)
# =============================================================================

MONGODB_NOTIFICATION_LOGS = [
    {
        "_id": "65a1b2c3d4e5f6789012345a",
        "event_type": "user.created",
        "channel": "email",
        "status": "sent",
        "recipient": "john@example.com",
        "data": {"user_id": 1, "username": "johndoe"},
        "timestamp": datetime(2024, 1, 1, 10, 0, 0),
    },
    {
        "_id": "65a1b2c3d4e5f6789012345b",
        "event_type": "user.created",
        "channel": "telegram",
        "status": "sent",
        "recipient": "chat_123456",
        "data": {"user_id": 1, "username": "johndoe"},
        "timestamp": datetime(2024, 1, 1, 10, 0, 1),
    },
    {
        "_id": "65a1b2c3d4e5f6789012345c",
        "event_type": "product.created",
        "channel": "telegram",
        "status": "sent",
        "recipient": "chat_123456",
        "data": {"product_id": 1, "name": "Wireless Bluetooth Headphones"},
        "timestamp": datetime(2024, 1, 2, 14, 30, 0),
    },
    {
        "_id": "65a1b2c3d4e5f6789012345d",
        "event_type": "ai.description.generated",
        "channel": "telegram",
        "status": "sent",
        "recipient": "chat_123456",
        "data": {"product_id": 1, "description": "Premium headphones..."},
        "timestamp": datetime(2024, 1, 2, 14, 35, 0),
    },
    {
        "_id": "65a1b2c3d4e5f6789012345e",
        "event_type": "user.created",
        "channel": "email",
        "status": "failed",
        "recipient": "invalid@email",
        "data": {"user_id": 99, "error": "Invalid email"},
        "timestamp": datetime(2024, 1, 3, 9, 0, 0),
    },
]


# =============================================================================
# Fixtures - RabbitMQ
# =============================================================================

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


# =============================================================================
# Fixtures - Telegram
# =============================================================================

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
def mock_telegram_disabled():
    """Mock disabled Telegram service."""
    with patch("app.telegram.telegram_service") as mock:
        mock.enabled = False
        mock.send_event_notification = AsyncMock(return_value=False)
        mock.send_message = AsyncMock(return_value=False)
        mock.close = AsyncMock()
        yield mock


# =============================================================================
# Fixtures - MongoDB
# =============================================================================

@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client with notification logs."""
    logs_data = list(MONGODB_NOTIFICATION_LOGS)

    collection = AsyncMock()

    async def mock_insert_one(doc):
        doc["_id"] = f"65a1b2c3d4e5f678901234{len(logs_data):02x}"
        doc["timestamp"] = datetime.utcnow()
        logs_data.append(doc)
        result = MagicMock()
        result.inserted_id = doc["_id"]
        return result

    async def mock_find_one(query):
        event_type = query.get("event_type")
        for doc in logs_data:
            if doc.get("event_type") == event_type:
                return doc
        return None

    def mock_find(query=None):
        cursor = MagicMock()
        filtered = logs_data
        if query:
            if "event_type" in query:
                filtered = [d for d in logs_data if d.get("event_type") == query["event_type"]]
            if "status" in query:
                filtered = [d for d in filtered if d.get("status") == query["status"]]

        async def to_list(length=None):
            return filtered[:length] if length else filtered

        cursor.to_list = AsyncMock(side_effect=to_list)
        cursor.sort = MagicMock(return_value=cursor)
        cursor.limit = MagicMock(return_value=cursor)
        return cursor

    collection.insert_one = AsyncMock(side_effect=mock_insert_one)
    collection.find_one = AsyncMock(side_effect=mock_find_one)
    collection.find = MagicMock(side_effect=mock_find)
    collection.count_documents = AsyncMock(return_value=len(logs_data))

    db = MagicMock()
    db.notification_logs = collection
    db.__getitem__ = MagicMock(return_value=collection)

    with patch("app.mongodb.get_mongodb") as mock_get_db:
        mock_get_db.return_value = db
        yield db


@pytest.fixture
def mock_mongodb_empty():
    """Mock MongoDB client with no data."""
    collection = AsyncMock()
    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="new_id"))
    collection.find_one = AsyncMock(return_value=None)
    collection.find = MagicMock(return_value=MagicMock(
        to_list=AsyncMock(return_value=[]),
        sort=MagicMock(return_value=MagicMock(
            limit=MagicMock(return_value=MagicMock(
                to_list=AsyncMock(return_value=[])
            ))
        ))
    ))
    collection.count_documents = AsyncMock(return_value=0)

    db = MagicMock()
    db.notification_logs = collection
    db.__getitem__ = MagicMock(return_value=collection)

    with patch("app.mongodb.get_mongodb") as mock_get_db:
        mock_get_db.return_value = db
        yield db


# =============================================================================
# Fixtures - Sample Events
# =============================================================================

@pytest.fixture
def sample_user_created_event():
    """Sample user.created event data."""
    return {
        "event_type": "user.created",
        "data": SAMPLE_USERS[0].copy(),
    }


@pytest.fixture
def sample_user_updated_event():
    """Sample user.updated event data."""
    user = SAMPLE_USERS[0].copy()
    user["full_name"] = "John Updated"
    return {
        "event_type": "user.updated",
        "data": user,
    }


@pytest.fixture
def sample_user_deleted_event():
    """Sample user.deleted event data."""
    return {
        "event_type": "user.deleted",
        "data": {"id": 1, "username": "johndoe"},
    }


@pytest.fixture
def sample_product_created_event():
    """Sample product.created event data."""
    return {
        "event_type": "product.created",
        "data": SAMPLE_PRODUCTS[0].copy(),
    }


@pytest.fixture
def sample_product_updated_event():
    """Sample product.updated event data."""
    product = SAMPLE_PRODUCTS[0].copy()
    product["price"] = "89.99"
    return {
        "event_type": "product.updated",
        "data": product,
    }


@pytest.fixture
def sample_ai_description_event():
    """Sample ai.description.generated event data."""
    return {
        "event_type": "ai.description.generated",
        "data": {
            "product_id": 1,
            "description": "Experience premium sound quality with these headphones.",
            "cached": False,
        },
    }


@pytest.fixture
def sample_ai_description_cached_event():
    """Sample ai.description.generated event with cached description."""
    return {
        "event_type": "ai.description.generated",
        "data": {
            "product_id": 1,
            "description": "Cached description for the product.",
            "cached": True,
        },
    }


# =============================================================================
# Fixtures - Sample Data Collections
# =============================================================================

@pytest.fixture
def sample_users():
    """All sample users."""
    return [u.copy() for u in SAMPLE_USERS]


@pytest.fixture
def sample_products():
    """All sample products."""
    return [p.copy() for p in SAMPLE_PRODUCTS]


@pytest.fixture
def sample_notification_logs():
    """All sample notification logs."""
    return [l.copy() for l in MONGODB_NOTIFICATION_LOGS]
