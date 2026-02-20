"""Unit tests for user query handlers."""

import pytest
from unittest.mock import AsyncMock

from app.application.queries.user_queries import GetUserQuery, ListUsersQuery
from app.application.handlers.query_handlers import GetUserQueryHandler, ListUsersQueryHandler
from app.domain.entities.user import User
from app.domain.exceptions import UserNotFoundError


@pytest.mark.asyncio
async def test_get_user_cache_hit(mock_uow, mock_user_cache):
    mock_user_cache.get = AsyncMock(return_value={
        "id": 1, "email": "test@example.com", "username": "testuser",
        "full_name": "Test User", "is_active": True,
        "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
    })

    handler = GetUserQueryHandler(mock_uow, mock_user_cache)
    result = await handler.handle(GetUserQuery(user_id=1))

    assert result.id == 1
    mock_uow.users.get_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_get_user_cache_miss(mock_uow, mock_user_cache):
    user = User(id=1, email="test@example.com", username="testuser", full_name="Test User")
    mock_uow.users.get_by_id = AsyncMock(return_value=user)

    handler = GetUserQueryHandler(mock_uow, mock_user_cache)
    result = await handler.handle(GetUserQuery(user_id=1))

    assert result.id == 1
    mock_user_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_not_found(mock_uow, mock_user_cache):
    handler = GetUserQueryHandler(mock_uow, mock_user_cache)

    with pytest.raises(UserNotFoundError):
        await handler.handle(GetUserQuery(user_id=999))


@pytest.mark.asyncio
async def test_list_users(mock_uow):
    users = [
        User(id=1, email="a@example.com", username="user1", full_name="User 1"),
        User(id=2, email="b@example.com", username="user2", full_name="User 2"),
    ]
    mock_uow.users.list_users = AsyncMock(return_value=users)
    mock_uow.users.count = AsyncMock(return_value=2)

    handler = ListUsersQueryHandler(mock_uow)
    result_users, total = await handler.handle(ListUsersQuery())

    assert len(result_users) == 2
    assert total == 2
