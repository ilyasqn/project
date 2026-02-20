"""Event handler classes with DI-injected services."""

import logging
from typing import Any

from ...domain.ports.services import (
    EmailNotificationService,
    NotificationLogRepository,
    TelegramNotificationService,
)

logger = logging.getLogger(__name__)


class BaseEventHandler:
    event_type: str = ""
    _email_method: str | None = None

    def __init__(
        self,
        email_service: EmailNotificationService | None = None,
        telegram_service: TelegramNotificationService | None = None,
        log_repo: NotificationLogRepository | None = None,
    ):
        self._email = email_service
        self._telegram = telegram_service
        self._log = log_repo

    async def handle(self, data: dict[str, Any]) -> None:
        payload = data.get("data", {})
        logger.info(f"Handling {self.event_type} event for {payload.get('id')}")

        if self._email_method and self._email:
            email_fn = getattr(self._email, self._email_method)
            success = await email_fn(payload)
            await self._log.log(self.event_type, "email", "sent" if success else "failed", payload)

        tg_success = await self._telegram.send_event_notification(self.event_type, payload)
        await self._log.log(self.event_type, "telegram", "sent" if tg_success else "failed", payload)


class UserCreatedEventHandler(BaseEventHandler):
    event_type = "user.created"
    _email_method = "send_welcome_email"


class UserUpdatedEventHandler(BaseEventHandler):
    event_type = "user.updated"
    _email_method = "send_user_update_notification"


class UserDeletedEventHandler(BaseEventHandler):
    event_type = "user.deleted"
    _email_method = "send_account_deletion_confirmation"


class ProductCreatedEventHandler(BaseEventHandler):
    event_type = "product.created"
    _email_method = "send_new_product_notification"


class ProductUpdatedEventHandler(BaseEventHandler):
    event_type = "product.updated"
    _email_method = "send_product_update_notification"


class ProductDeletedEventHandler(BaseEventHandler):
    event_type = "product.deleted"
