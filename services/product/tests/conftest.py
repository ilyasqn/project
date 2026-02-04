"""Pytest fixtures for Product Service tests."""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add paths for imports
sys.path.insert(0, "/app")


# =============================================================================
# Sample Data - Products
# =============================================================================

SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "name": "Wireless Bluetooth Headphones",
        "description": "High-quality wireless headphones with noise cancellation.",
        "price": "99.99",
        "sku": "WBH-001",
        "stock_quantity": 50,
        "category": "Electronics",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    },
    {
        "id": 2,
        "name": "Mechanical Gaming Keyboard",
        "description": "RGB mechanical keyboard with Cherry MX switches.",
        "price": "149.99",
        "sku": "MGK-002",
        "stock_quantity": 30,
        "category": "Electronics",
        "is_active": True,
        "created_at": "2024-01-02T00:00:00",
        "updated_at": "2024-01-02T00:00:00",
    },
    {
        "id": 3,
        "name": "Ergonomic Office Chair",
        "description": "Comfortable office chair with lumbar support.",
        "price": "299.99",
        "sku": "EOC-003",
        "stock_quantity": 20,
        "category": "Furniture",
        "is_active": True,
        "created_at": "2024-01-03T00:00:00",
        "updated_at": "2024-01-03T00:00:00",
    },
    {
        "id": 4,
        "name": "USB-C Hub",
        "description": None,  # No description - for AI generation tests
        "price": "49.99",
        "sku": "UCH-004",
        "stock_quantity": 100,
        "category": "Electronics",
        "is_active": True,
        "created_at": "2024-01-04T00:00:00",
        "updated_at": "2024-01-04T00:00:00",
    },
    {
        "id": 5,
        "name": "Standing Desk",
        "description": "Electric standing desk with memory presets.",
        "price": "499.99",
        "sku": "STD-005",
        "stock_quantity": 15,
        "category": "Furniture",
        "is_active": True,
        "created_at": "2024-01-05T00:00:00",
        "updated_at": "2024-01-05T00:00:00",
    },
]


# =============================================================================
# Redis Mock Data
# =============================================================================

REDIS_CACHE_DATA = {
    "product:1": '{"id": 1, "name": "Wireless Bluetooth Headphones", "price": "99.99"}',
    "product:2": '{"id": 2, "name": "Mechanical Gaming Keyboard", "price": "149.99"}',
    "product:3": '{"id": 3, "name": "Ergonomic Office Chair", "price": "299.99"}',
}


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
# Fixtures - Redis
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client with sample data."""
    async def mock_get(key):
        return REDIS_CACHE_DATA.get(key)

    async def mock_setex(key, ttl, value):
        REDIS_CACHE_DATA[key] = value
        return True

    async def mock_delete(key):
        if key in REDIS_CACHE_DATA:
            del REDIS_CACHE_DATA[key]
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
    """Mock Redis client with no data (cache miss)."""
    with patch("app.redis_cache.get_redis") as mock:
        client = AsyncMock()
        client.get = AsyncMock(return_value=None)
        client.setex = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        client.close = AsyncMock()
        mock.return_value = client
        yield client


# =============================================================================
# Fixtures - PostgreSQL Database
# =============================================================================

def create_mock_product(product_data):
    """Create a mock product object from dict."""
    mock_product = MagicMock()
    for key, value in product_data.items():
        setattr(mock_product, key, value)
    mock_product.to_dict = MagicMock(return_value=product_data)
    return mock_product


@pytest.fixture
def mock_database():
    """Mock database session with sample products."""
    products_db = {p["id"]: create_mock_product(p) for p in SAMPLE_PRODUCTS}

    session = AsyncMock()

    async def mock_execute(query):
        result = MagicMock()
        # Check if it's a select query for a specific product
        if hasattr(query, 'whereclause'):
            # Return first product for simplicity
            result.scalar_one_or_none = MagicMock(return_value=products_db.get(1))
            result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=list(products_db.values()))))
        else:
            result.scalar_one_or_none = MagicMock(return_value=products_db.get(1))
            result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=list(products_db.values()))))
        return result

    async def mock_get(model, product_id):
        return products_db.get(product_id)

    session.execute = AsyncMock(side_effect=mock_execute)
    session.get = AsyncMock(side_effect=mock_get)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    session.close = AsyncMock()

    return session


@pytest.fixture
def mock_db_session(mock_database):
    """Mock the get_db dependency."""
    async def mock_get_db():
        yield mock_database

    with patch("app.routes.get_db", mock_get_db), \
         patch("app.handlers.async_session_maker") as mock_session_maker:

        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_database)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
        yield mock_database


# =============================================================================
# Fixtures - Sample Data
# =============================================================================

@pytest.fixture
def sample_product():
    """Sample product data."""
    return SAMPLE_PRODUCTS[0].copy()


@pytest.fixture
def sample_product_no_description():
    """Sample product without description."""
    return SAMPLE_PRODUCTS[3].copy()


@pytest.fixture
def sample_products():
    """All sample products."""
    return [p.copy() for p in SAMPLE_PRODUCTS]


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


@pytest.fixture
def sample_product_created_event():
    """Sample product.created event data."""
    return {
        "event_type": "product.created",
        "data": SAMPLE_PRODUCTS[3].copy(),  # Product without description
    }
