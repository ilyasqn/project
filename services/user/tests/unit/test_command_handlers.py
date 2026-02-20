"""Unit tests for user command handlers."""

import pytest
from unittest.mock import AsyncMock

from app.application.commands.user_commands import CreateUserCommand, UpdateUserCommand, DeleteUserCommand
from app.application.handlers.command_handlers import (
    CreateUserCommandHandler,
    UpdateUserCommandHandler,
    DeleteUserCommandHandler,
)
from app.domain.entities.user import User
from app.domain.exceptions import UserAlreadyExistsError, UserNotFoundError


@pytest.mark.asyncio
async def test_create_user_success(mock_uow, mock_event_publisher, mock_user_cache):
    created_user = User(id=1, email="test@example.com", username="testuser", full_name="Test User")
    mock_uow.users.create = AsyncMock(return_value=created_user)

    handler = CreateUserCommandHandler(mock_uow, mock_event_publisher, mock_user_cache)

    command = CreateUserCommand(
        email="test@example.com", username="testuser",
        full_name="Test User", password="password123",
    )
    result = await handler.handle(command)

    assert result.id == 1
    assert result.email == "test@example.com"
    mock_uow.users.create.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(mock_uow, mock_event_publisher, mock_user_cache):
    mock_uow.users.get_by_email = AsyncMock(
        return_value=User(id=1, email="test@example.com")
    )

    handler = CreateUserCommandHandler(mock_uow, mock_event_publisher, mock_user_cache)

    command = CreateUserCommand(
        email="test@example.com", username="testuser",
        full_name="Test User", password="password123",
    )

    with pytest.raises(UserAlreadyExistsError):
        await handler.handle(command)


@pytest.mark.asyncio
async def test_update_user_not_found(mock_uow, mock_event_publisher, mock_user_cache):
    handler = UpdateUserCommandHandler(mock_uow, mock_event_publisher, mock_user_cache)

    command = UpdateUserCommand(user_id=999, full_name="New Name")

    with pytest.raises(UserNotFoundError):
        await handler.handle(command)


@pytest.mark.asyncio
async def test_delete_user_success(mock_uow, mock_event_publisher, mock_user_cache):
    existing_user = User(id=1, email="test@example.com", username="testuser", full_name="Test User")
    mock_uow.users.get_by_id = AsyncMock(return_value=existing_user)

    handler = DeleteUserCommandHandler(mock_uow, mock_event_publisher, mock_user_cache)

    command = DeleteUserCommand(user_id=1)
    await handler.handle(command)

    mock_uow.users.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()
    mock_user_cache.delete.assert_called_once_with(1)
    mock_event_publisher.publish.assert_called_once()
