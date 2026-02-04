"""Pytest fixtures for AI Service tests."""

import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


# =============================================================================
# Sample Data - Products
# =============================================================================

SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "name": "Wireless Bluetooth Headphones",
        "description": None,
        "price": "99.99",
        "sku": "WBH-001",
        "category": "Electronics",
        "is_active": True,
    },
    {
        "id": 2,
        "name": "Mechanical Gaming Keyboard",
        "description": "RGB mechanical keyboard with Cherry MX switches.",
        "price": "149.99",
        "sku": "MGK-002",
        "category": "Electronics",
        "is_active": True,
    },
    {
        "id": 3,
        "name": "Ergonomic Office Chair",
        "description": None,
        "price": "299.99",
        "sku": "EOC-003",
        "category": "Furniture",
        "is_active": True,
    },
    {
        "id": 4,
        "name": "USB-C Hub",
        "description": None,
        "price": "49.99",
        "sku": "UCH-004",
        "category": "Electronics",
        "is_active": True,
    },
    {
        "id": 5,
        "name": "Standing Desk",
        "description": "Electric standing desk with memory presets.",
        "price": "499.99",
        "sku": "STD-005",
        "category": "Furniture",
        "is_active": True,
    },
]


# =============================================================================
# Sample Data - AI Generation History (MongoDB)
# =============================================================================

MONGODB_GENERATION_HISTORY = [
    {
        "_id": "65a1b2c3d4e5f6789012345a",
        "product_id": 1,
        "product_name": "Wireless Bluetooth Headphones",
        "prompt": "Generate a product description for: Wireless Bluetooth Headphones, category: Electronics",
        "description": "Experience premium sound quality with our Wireless Bluetooth Headphones.",
        "model": "gpt-3.5-turbo",
        "tokens_used": 150,
        "created_at": datetime(2024, 1, 1, 10, 0, 0),
    },
    {
        "_id": "65a1b2c3d4e5f6789012345b",
        "product_id": 3,
        "product_name": "Ergonomic Office Chair",
        "prompt": "Generate a product description for: Ergonomic Office Chair, category: Furniture",
        "description": "Upgrade your workspace with our premium Ergonomic Office Chair.",
        "model": "gpt-3.5-turbo",
        "tokens_used": 145,
        "created_at": datetime(2024, 1, 2, 14, 30, 0),
    },
    {
        "_id": "65a1b2c3d4e5f6789012345c",
        "product_id": 4,
        "product_name": "USB-C Hub",
        "prompt": "Generate a product description for: USB-C Hub, category: Electronics",
        "description": "Expand your connectivity with our versatile USB-C Hub.",
        "model": "gpt-3.5-turbo",
        "tokens_used": 120,
        "created_at": datetime(2024, 1, 3, 9, 15, 0),
    },
]


# =============================================================================
# Sample Data - Redis Cache
# =============================================================================

REDIS_DESCRIPTION_CACHE = {
    "ai:description:1": "Experience premium sound quality with our Wireless Bluetooth Headphones.",
    "ai:description:3": "Upgrade your workspace with our premium Ergonomic Office Chair.",
}


# =============================================================================
# Fixtures - LLM Client
# =============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client with realistic responses."""
    mock = MagicMock()
    mock.model = "gpt-3.5-turbo"

    async def generate_description(prompt, **kwargs):
        # Return different descriptions based on product in prompt
        if "Headphones" in prompt:
            return "Experience premium sound quality with our Wireless Bluetooth Headphones."
        elif "Keyboard" in prompt:
            return "Dominate your games with our Mechanical Gaming Keyboard."
        elif "Chair" in prompt:
            return "Upgrade your workspace with our premium Ergonomic Office Chair."
        elif "USB-C" in prompt:
            return "Expand your connectivity with our versatile USB-C Hub."
        elif "Desk" in prompt:
            return "Transform your work habits with our Electric Standing Desk."
        return "A high-quality product designed for excellence."

    mock.generate = AsyncMock(side_effect=generate_description)
    mock.summarize = AsyncMock(return_value="Summary of the text.")
    mock.analyze = AsyncMock(
        return_value={"sentiment": "positive", "confidence": 0.9}
    )
    return mock


# =============================================================================
# Fixtures - MongoDB
# =============================================================================

@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client with sample generation history."""
    history_data = list(MONGODB_GENERATION_HISTORY)

    collection = AsyncMock()

    async def mock_insert_one(doc):
        doc["_id"] = f"65a1b2c3d4e5f678901234{len(history_data):02x}"
        history_data.append(doc)
        result = MagicMock()
        result.inserted_id = doc["_id"]
        return result

    async def mock_find_one(query):
        product_id = query.get("product_id")
        for doc in history_data:
            if doc.get("product_id") == product_id:
                return doc
        return None

    def mock_find(query=None):
        cursor = AsyncMock()
        cursor.to_list = AsyncMock(return_value=history_data)
        cursor.sort = MagicMock(return_value=cursor)
        cursor.limit = MagicMock(return_value=cursor)
        return cursor

    collection.insert_one = AsyncMock(side_effect=mock_insert_one)
    collection.find_one = AsyncMock(side_effect=mock_find_one)
    collection.find = MagicMock(side_effect=mock_find)
    collection.count_documents = AsyncMock(return_value=len(history_data))

    db = MagicMock()
    db.generation_history = collection
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
    collection.find = MagicMock(return_value=AsyncMock(to_list=AsyncMock(return_value=[])))
    collection.count_documents = AsyncMock(return_value=0)

    db = MagicMock()
    db.generation_history = collection
    db.__getitem__ = MagicMock(return_value=collection)

    with patch("app.mongodb.get_mongodb") as mock_get_db:
        mock_get_db.return_value = db
        yield db


# =============================================================================
# Fixtures - Redis
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client with cached descriptions."""
    cache_data = dict(REDIS_DESCRIPTION_CACHE)

    async def mock_get(key):
        return cache_data.get(key)

    async def mock_setex(key, ttl, value):
        cache_data[key] = value
        return True

    async def mock_delete(key):
        if key in cache_data:
            del cache_data[key]
        return True

    with patch("app.redis_cache.get_redis") as mock:
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)
        client.setex = AsyncMock(side_effect=mock_setex)
        client.delete = AsyncMock(side_effect=mock_delete)
        client.close = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_redis_empty():
    """Mock Redis client with no cached data."""
    with patch("app.redis_cache.get_redis") as mock:
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        client.close = AsyncMock()
        mock.return_value = client
        yield client


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
# Fixtures - Sample Events
# =============================================================================

@pytest.fixture
def sample_product_created_event():
    """Sample product.created event data (no description)."""
    return {
        "event_type": "product.created",
        "data": SAMPLE_PRODUCTS[0].copy(),
    }


@pytest.fixture
def sample_product_with_description_event():
    """Sample product.created event with existing description."""
    return {
        "event_type": "product.created",
        "data": SAMPLE_PRODUCTS[1].copy(),
    }


@pytest.fixture
def sample_products():
    """All sample products."""
    return [p.copy() for p in SAMPLE_PRODUCTS]


@pytest.fixture
def sample_generation_history():
    """Sample MongoDB generation history."""
    return [h.copy() for h in MONGODB_GENERATION_HISTORY]
