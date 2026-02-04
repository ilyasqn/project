"""Integration test fixtures."""

import asyncio
import sys
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add paths for imports
sys.path.insert(0, "/app")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_rabbitmq_client():
    """Mock RabbitMQ client for integration tests."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.publish = AsyncMock()
    client.subscribe = AsyncMock()
    client.exchange = MagicMock()
    return client


@pytest.fixture
def mock_mongodb_client():
    """Mock MongoDB client for integration tests."""
    client = AsyncMock()
    db = AsyncMock()

    # Mock collections
    db.ai_generation_history = AsyncMock()
    db.ai_generation_history.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id="test_id")
    )
    db.ai_generation_history.find_one = AsyncMock(return_value=None)

    db.notification_logs = AsyncMock()
    db.notification_logs.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id="test_id")
    )

    client.__getitem__ = MagicMock(return_value=db)
    return client, db


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for integration tests."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for integration tests."""
    client = AsyncMock()
    client.generate = AsyncMock(
        return_value="An excellent product designed for your needs."
    )
    return client


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for integration tests."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.session = AsyncMock()
    bot.session.close = AsyncMock()
    return bot
