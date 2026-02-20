"""User repository port (abstract interface).

This is a PORT in Clean Architecture — it defines WHAT the application needs,
not HOW it's done. The concrete implementation lives in:
    infrastructure/persistence/repositories.py -> SQLAlchemyUserRepository

The application layer (handlers) depends on this interface, never on SQLAlchemy directly.
"""

from abc import ABC, abstractmethod

from ..entities.user import User


class UserRepository(ABC):
    """Abstract interface for user persistence operations."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        raise NotImplementedError
