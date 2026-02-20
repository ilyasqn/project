"""Product service test fixtures."""

import asyncio
from unittest.mock import AsyncMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_product_repository():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_sku = AsyncMock(return_value=None)
    repo.list_products = AsyncMock(return_value=[])
    repo.count = AsyncMock(return_value=0)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_product_repository):
    uow = AsyncMock()
    uow.products = mock_product_repository
    uow.commit = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.fixture
def mock_product_cache():
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def mock_event_publisher():
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    publisher.close = AsyncMock()
    return publisher


@pytest.fixture
def mock_llm_service():
    llm = AsyncMock()
    llm.generate_description = AsyncMock(
        return_value="An excellent product designed for your needs."
    )
    return llm


@pytest.fixture
def mock_history_repo():
    repo = AsyncMock()
    repo.save = AsyncMock(return_value="test_id")
    repo.get_by_product_id = AsyncMock(return_value=[])
    return repo
