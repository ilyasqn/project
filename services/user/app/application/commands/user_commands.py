"""User command definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    username: str
    full_name: str
    password: str


@dataclass(frozen=True)
class UpdateUserCommand:
    user_id: int
    email: str | None = None
    username: str | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class DeleteUserCommand:
    user_id: int
