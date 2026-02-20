"""Notification service ports (abstract interfaces).

EmailNotificationService — Concrete: infrastructure/external/email_adapter.py -> EmailServiceAdapter
TelegramNotificationService — Concrete: infrastructure/external/telegram_adapter.py -> TelegramServiceAdapter
NotificationLogRepository — Concrete: infrastructure/external/mongodb_adapter.py -> MongoNotificationLogRepository
"""

from abc import ABC, abstractmethod
from typing import Any


class EmailNotificationService(ABC):
    """Abstract interface for sending email notifications."""

    @abstractmethod
    async def send_welcome_email(self, user_data: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_user_update_notification(self, user_data: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_account_deletion_confirmation(self, user_data: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_new_product_notification(self, product_data: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_product_update_notification(self, product_data: dict[str, Any]) -> bool:
        raise NotImplementedError


class TelegramNotificationService(ABC):
    """Abstract interface for sending Telegram notifications."""

    @abstractmethod
    async def send_event_notification(self, event_type: str, data: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError


class NotificationLogRepository(ABC):
    """Abstract interface for logging notification delivery to MongoDB."""

    @abstractmethod
    async def log(self, event_type: str, channel: str, status: str, data: dict[str, Any], error: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self, event_type: str | None = None, channel: str | None = None, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
