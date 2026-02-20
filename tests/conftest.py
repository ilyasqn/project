"""Integration test fixtures."""

import asyncio
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, "/app")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user_repository():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_email = AsyncMock(return_value=None)
    repo.get_by_username = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_user_uow(mock_user_repository):
    uow = AsyncMock()
    uow.users = mock_user_repository
    uow.commit = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.fixture
def mock_product_repository():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_sku = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_product_uow(mock_product_repository):
    uow = AsyncMock()
    uow.products = mock_product_repository
    uow.commit = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.fixture
def mock_event_publisher():
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    publisher.close = AsyncMock()
    return publisher


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


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


@pytest.fixture
def mock_email_service():
    service = AsyncMock()
    service.send_welcome_email = AsyncMock(return_value=True)
    service.send_new_product_notification = AsyncMock(return_value=True)
    service.send_user_update_notification = AsyncMock(return_value=True)
    service.send_account_deletion_confirmation = AsyncMock(return_value=True)
    service.send_product_update_notification = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_telegram_service():
    service = AsyncMock()
    service.send_event_notification = AsyncMock(return_value=True)
    service.close = AsyncMock()
    service.enabled = True
    return service


@pytest.fixture
def mock_log_repo():
    repo = AsyncMock()
    repo.log = AsyncMock(return_value="test_id")
    repo.get_logs = AsyncMock(return_value=[])
    repo.get_stats = AsyncMock(return_value={})
    repo.close = AsyncMock()
    return repo
