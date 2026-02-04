"""Tests for Product Service API routes."""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch


# Create mock session at module level
def create_mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_session():
    """Mock database session fixture."""
    return create_mock_session()


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch("app.main.init_db", new_callable=AsyncMock), \
         patch("app.main.start_consuming", new_callable=AsyncMock), \
         patch("app.main.close_consumer", new_callable=AsyncMock), \
         patch("app.main.close_publisher", new_callable=AsyncMock), \
         patch("app.main.close_redis", new_callable=AsyncMock), \
         patch("app.events.get_publisher") as mock_pub:
        publisher = AsyncMock()
        publisher.publish = AsyncMock()
        mock_pub.return_value = publisher
        yield


@pytest.fixture
async def client(mock_dependencies, mock_session):
    """Create test client with mocked database."""
    from app.main import app
    from app.database import get_db

    # Override the get_db dependency
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "product"


@pytest.mark.asyncio
async def test_get_product_uses_cache(client, sample_product):
    """Test that get_product uses Redis cache."""
    with patch("app.routes.get_cached_product", new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = sample_product

        response = await client.get("/products/1")

        mock_cache.assert_called_once_with(1)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_product_cache_miss(client, mock_session, sample_product):
    """Test that get_product fetches from DB on cache miss."""
    # Create mock product
    mock_product = MagicMock()
    for key, value in sample_product.items():
        setattr(mock_product, key, value)
    mock_product.to_dict.return_value = sample_product

    # Mock database result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_product
    mock_session.execute.return_value = mock_result

    with patch("app.routes.get_cached_product", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.routes.cache_product", new_callable=AsyncMock):
        mock_cache_get.return_value = None

        response = await client.get("/products/1")

        mock_cache_get.assert_called_once_with(1)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_product_not_found(client, mock_session):
    """Test getting a non-existent product."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("app.routes.get_cached_product", new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = None

        response = await client.get("/products/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"


@pytest.mark.asyncio
async def test_create_product(client, mock_session, sample_product):
    """Test creating a new product."""
    from datetime import datetime

    # Mock no existing product with same SKU
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Mock the refresh to set ID
    async def mock_refresh(product):
        product.id = 1
        product.is_active = True
        product.created_at = datetime(2024, 1, 1, 0, 0, 0)
        product.updated_at = datetime(2024, 1, 1, 0, 0, 0)

    mock_session.refresh = mock_refresh

    with patch("app.routes.publish_product_event", new_callable=AsyncMock):
        response = await client.post("/products/", json={
            "name": "Wireless Bluetooth Headphones",
            "price": 99.99,
            "sku": "WBH-NEW",
            "category": "Electronics",
        })

        assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_products(client, mock_session, sample_products):
    """Test listing all products."""
    mock_products = []
    for p in sample_products:
        mock_product = MagicMock()
        for key, value in p.items():
            setattr(mock_product, key, value)
        mock_products.append(mock_product)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_products
    mock_session.execute.return_value = mock_result

    response = await client.get("/products/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_product(client, mock_session, sample_product):
    """Test updating a product."""
    mock_product = MagicMock()
    for key, value in sample_product.items():
        setattr(mock_product, key, value)
    mock_product.to_dict.return_value = sample_product

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_product
    mock_session.execute.return_value = mock_result

    with patch("app.routes.publish_product_event", new_callable=AsyncMock):
        response = await client.put("/products/1", json={
            "price": 89.99,
        })

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_product(client, mock_session, sample_product):
    """Test deleting a product."""
    mock_product = MagicMock()
    for key, value in sample_product.items():
        setattr(mock_product, key, value)
    mock_product.to_dict.return_value = sample_product

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_product
    mock_session.execute.return_value = mock_result

    with patch("app.routes.publish_product_event", new_callable=AsyncMock):
        response = await client.delete("/products/1")

        assert response.status_code == 204
