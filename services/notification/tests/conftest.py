"""Notification service test fixtures."""

import asyncio
from unittest.mock import AsyncMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_email_service():
    service = AsyncMock()
    service.send_welcome_email = AsyncMock(return_value=True)
    service.send_user_update_notification = AsyncMock(return_value=True)
    service.send_account_deletion_confirmation = AsyncMock(return_value=True)
    service.send_new_product_notification = AsyncMock(return_value=True)
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
