"""Hashed password value object using bcrypt."""

from dataclasses import dataclass

import bcrypt


@dataclass(frozen=True)
class HashedPassword:
    value: str

    @classmethod
    def from_plain(cls, plain_password: str) -> "HashedPassword":
        hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
        return cls(value=hashed.decode())

    def verify(self, plain_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), self.value.encode())
