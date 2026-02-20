"""User query definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetUserQuery:
    user_id: int


@dataclass(frozen=True)
class ListUsersQuery:
    skip: int = 0
    limit: int = 100
