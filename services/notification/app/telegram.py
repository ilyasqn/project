"""Telegram notification service using aiogram."""

import logging
import os
from typing import Any

from aiogram import Bot
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


class TelegramService:
    """Telegram notification service."""

    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
        self.chat_id = TELEGRAM_CHAT_ID
        self._enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

        if not self._enabled:
            logger.warning(
                "Telegram notifications disabled: "
                "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured"
            )

    @property
    def enabled(self) -> bool:
        """Check if Telegram notifications are enabled."""
        return self._enabled

    async def close(self) -> None:
        """Close the bot session."""
        if self.bot:
            await self.bot.session.close()

    async def send_message(self, text: str, parse_mode: str = ParseMode.HTML) -> bool:
        """
        Send a message to the configured chat.

        Args:
            text: The message text
            parse_mode: Parse mode for formatting (HTML by default)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._enabled:
            logger.debug(f"[TELEGRAM DISABLED] Would send: {text[:100]}...")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            logger.info(f"[TELEGRAM] Sent message to chat {self.chat_id}")
            return True

        except Exception as e:
            logger.error(f"[TELEGRAM] Failed to send message: {e}")
            return False

    async def send_event_notification(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> bool:
        """
        Send an event notification to Telegram.

        Args:
            event_type: Type of the event
            data: Event data

        Returns:
            True if sent successfully, False otherwise
        """
        message = self._format_event_message(event_type, data)
        return await self.send_message(message)

    def _format_event_message(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> str:
        """
        Format event data into a Telegram message.

        Args:
            event_type: Type of the event
            data: Event data

        Returns:
            Formatted message string
        """
        emoji_map = {
            "user.created": "\U0001F464",       # person silhouette
            "user.updated": "\u270F\uFE0F",     # pencil
            "user.deleted": "\U0001F5D1\uFE0F", # wastebasket
            "product.created": "\U0001F4E6",    # package
            "product.updated": "\U0001F504",    # counterclockwise arrows
            "product.deleted": "\u274C",        # red X
            "ai.description.generated": "\U0001F916", # robot
        }

        emoji = emoji_map.get(event_type, "\U0001F4E2")  # loudspeaker

        # Build message header
        lines = [f"{emoji} <b>{event_type.upper()}</b>", ""]

        # Format data fields
        for key, value in data.items():
            if value is not None:
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                lines.append(f"<b>{key}:</b> {str_value}")

        return "\n".join(lines)


# Singleton instance
telegram_service = TelegramService()
