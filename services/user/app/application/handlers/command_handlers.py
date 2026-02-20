"""User command handlers.

Each handler does one use case:
  1. Open UoW transaction
  2. Run business logic
  3. Commit
  4. Publish events (after commit for consistency)
"""

import logging

from ...domain.entities.user import User
from ...domain.exceptions import UserAlreadyExistsError, UserNotFoundError
from ...domain.value_objects.hashed_password import HashedPassword
from ...infrastructure.cache.redis_adapter import RedisUserCache
from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQUserEventPublisher
from ...infrastructure.persistence.uow import UnitOfWork
from ..commands.user_commands import CreateUserCommand, DeleteUserCommand, UpdateUserCommand

logger = logging.getLogger(__name__)


class CreateUserCommandHandler:
    def __init__(self, uow: UnitOfWork, events: RabbitMQUserEventPublisher, cache: RedisUserCache):
        self._uow = uow
        self._events = events
        self._cache = cache

    async def handle(self, command: CreateUserCommand) -> User:
        async with self._uow:
            await self._check_unique_email(command.email)
            await self._check_unique_username(command.username)

            user = self._build_user(command)
            user = await self._uow.users.create(user)
            await self._uow.commit()

        await self._events.publish("user.created", {"event_type": "user.created", "data": user.to_dict()})
        logger.info(f"Created user {user.id}")
        return user

    async def _check_unique_email(self, email: str) -> None:
        if await self._uow.users.get_by_email(email):
            raise UserAlreadyExistsError("Email already registered")

    async def _check_unique_username(self, username: str) -> None:
        if await self._uow.users.get_by_username(username):
            raise UserAlreadyExistsError("Username already taken")

    def _build_user(self, command: CreateUserCommand) -> User:
        hashed = HashedPassword.from_plain(command.password)
        return User(
            email=command.email,
            username=command.username,
            full_name=command.full_name,
            hashed_password=hashed.value,
        )


class UpdateUserCommandHandler:
    def __init__(self, uow: UnitOfWork, events: RabbitMQUserEventPublisher, cache: RedisUserCache):
        self._uow = uow
        self._events = events
        self._cache = cache

    async def handle(self, command: UpdateUserCommand) -> User:
        async with self._uow:
            user = await self._uow.users.get_by_id(command.user_id)
            if not user:
                raise UserNotFoundError(f"User {command.user_id} not found")

            self._apply_changes(user, command)
            user = await self._uow.users.update(user)
            await self._uow.commit()

        await self._cache.delete(command.user_id)
        await self._events.publish("user.updated", {"event_type": "user.updated", "data": user.to_dict()})
        logger.info(f"Updated user {user.id}")
        return user

    def _apply_changes(self, user: User, command: UpdateUserCommand) -> None:
        for field in ("email", "username", "full_name", "is_active"):
            value = getattr(command, field)
            if value is not None:
                setattr(user, field, value)
        if command.password is not None:
            user.hashed_password = HashedPassword.from_plain(command.password).value


class DeleteUserCommandHandler:
    def __init__(self, uow: UnitOfWork, events: RabbitMQUserEventPublisher, cache: RedisUserCache):
        self._uow = uow
        self._events = events
        self._cache = cache

    async def handle(self, command: DeleteUserCommand) -> None:
        async with self._uow:
            user = await self._uow.users.get_by_id(command.user_id)
            if not user:
                raise UserNotFoundError(f"User {command.user_id} not found")

            user_data = user.to_dict()
            await self._uow.users.delete(command.user_id)
            await self._uow.commit()

        await self._cache.delete(command.user_id)
        await self._events.publish("user.deleted", {"event_type": "user.deleted", "data": user_data})
        logger.info(f"Deleted user {command.user_id}")
