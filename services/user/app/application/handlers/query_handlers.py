"""User query handlers (read-only operations)."""

import logging

from ...domain.entities.user import User
from ...domain.exceptions import UserNotFoundError
from ...infrastructure.cache.redis_adapter import RedisUserCache
from ...infrastructure.persistence.uow import UnitOfWork
from ..queries.user_queries import GetUserQuery, ListUsersQuery

logger = logging.getLogger(__name__)


class GetUserQueryHandler:
    def __init__(self, uow: UnitOfWork, cache: RedisUserCache):
        self._uow = uow
        self._cache = cache

    async def handle(self, query: GetUserQuery) -> User:
        cached = await self._cache.get(query.user_id)
        if cached:
            return User(**cached)

        async with self._uow:
            user = await self._uow.users.get_by_id(query.user_id)
            if not user:
                raise UserNotFoundError(f"User {query.user_id} not found")

        await self._cache.set(query.user_id, user.to_dict())
        return user


class ListUsersQueryHandler:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: ListUsersQuery) -> tuple[list[User], int]:
        async with self._uow:
            users = await self._uow.users.list_users(skip=query.skip, limit=query.limit)
            total = await self._uow.users.count()
        return users, total
