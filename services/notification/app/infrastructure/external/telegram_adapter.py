"""Telegram notification service adapter."""

import logging
from typing import Any

from aiogram import Bot
from aiogram.enums import ParseMode

from ...domain.ports.services import TelegramNotificationService

logger = logging.getLogger(__name__)


class TelegramServiceAdapter(TelegramNotificationService):
    def __init__(self, bot_token: str, chat_id: str):
        self._bot = Bot(token=bot_token) if bot_token else None
        self._chat_id = chat_id
        self._enabled = bool(bot_token and chat_id)

        if not self._enabled:
            logger.warning(
                "Telegram notifications disabled: "
                "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured"
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def close(self) -> None:
        if self._bot:
            await self._bot.session.close()

    async def send_event_notification(self, event_type: str, data: dict[str, Any]) -> bool:
        message = self._format_event_message(event_type, data)

        if not self._enabled:
            logger.debug(f"[TELEGRAM DISABLED] Would send: {message[:100]}...")
            return False

        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
            )
            logger.info(f"[TELEGRAM] Sent message to chat {self._chat_id}")
            return True
        except Exception as e:
            logger.error(f"[TELEGRAM] Failed to send message: {e}")
            return False

    def _format_event_message(self, event_type: str, data: dict[str, Any]) -> str:
        emoji_map = {
            "user.created": "\U0001F464",
            "user.updated": "\u270F\uFE0F",
            "user.deleted": "\U0001F5D1\uFE0F",
            "product.created": "\U0001F4E6",
            "product.updated": "\U0001F504",
            "product.deleted": "\u274C",
        }

        emoji = emoji_map.get(event_type, "\U0001F4E2")
        lines = [f"{emoji} <b>{event_type.upper()}</b>", ""]

        for key, value in data.items():
            if value is not None:
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                lines.append(f"<b>{key}:</b> {str_value}")

        return "\n".join(lines)
