"""Event handlers for processing RabbitMQ messages."""

import logging
from typing import Any

from .mongodb import log_notification
from .services import email_service
from .telegram import telegram_service

logger = logging.getLogger(__name__)


async def handle_user_created(data: dict[str, Any]) -> None:
    """Handle user.created event."""
    user_data = data.get("data", {})
    logger.info(f"Handling user.created event for user {user_data.get('id')}")

    # Send email notification
    email_success = await email_service.send_welcome_email(user_data)
    await log_notification(
        "user.created", "email",
        "sent" if email_success else "failed",
        user_data,
    )

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "user.created", user_data
    )
    await log_notification(
        "user.created", "telegram",
        "sent" if telegram_success else "failed",
        user_data,
    )


async def handle_user_updated(data: dict[str, Any]) -> None:
    """Handle user.updated event."""
    user_data = data.get("data", {})
    logger.info(f"Handling user.updated event for user {user_data.get('id')}")

    # Send email notification
    email_success = await email_service.send_user_update_notification(user_data)
    await log_notification(
        "user.updated", "email",
        "sent" if email_success else "failed",
        user_data,
    )

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "user.updated", user_data
    )
    await log_notification(
        "user.updated", "telegram",
        "sent" if telegram_success else "failed",
        user_data,
    )


async def handle_user_deleted(data: dict[str, Any]) -> None:
    """Handle user.deleted event."""
    user_data = data.get("data", {})
    logger.info(f"Handling user.deleted event for user {user_data.get('id')}")

    # Send email notification
    email_success = await email_service.send_account_deletion_confirmation(user_data)
    await log_notification(
        "user.deleted", "email",
        "sent" if email_success else "failed",
        user_data,
    )

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "user.deleted", user_data
    )
    await log_notification(
        "user.deleted", "telegram",
        "sent" if telegram_success else "failed",
        user_data,
    )


async def handle_product_created(data: dict[str, Any]) -> None:
    """Handle product.created event."""
    product_data = data.get("data", {})
    logger.info(f"Handling product.created event for product {product_data.get('id')}")

    # Send email notification
    email_success = await email_service.send_new_product_notification(product_data)
    await log_notification(
        "product.created", "email",
        "sent" if email_success else "failed",
        product_data,
    )

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "product.created", product_data
    )
    await log_notification(
        "product.created", "telegram",
        "sent" if telegram_success else "failed",
        product_data,
    )


async def handle_product_updated(data: dict[str, Any]) -> None:
    """Handle product.updated event."""
    product_data = data.get("data", {})
    logger.info(f"Handling product.updated event for product {product_data.get('id')}")

    # Send email notification
    email_success = await email_service.send_product_update_notification(product_data)
    await log_notification(
        "product.updated", "email",
        "sent" if email_success else "failed",
        product_data,
    )

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "product.updated", product_data
    )
    await log_notification(
        "product.updated", "telegram",
        "sent" if telegram_success else "failed",
        product_data,
    )


async def handle_product_deleted(data: dict[str, Any]) -> None:
    """Handle product.deleted event."""
    product_data = data.get("data", {})
    logger.info(f"Handling product.deleted event for product {product_data.get('id')}")

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "product.deleted", product_data
    )
    await log_notification(
        "product.deleted", "telegram",
        "sent" if telegram_success else "failed",
        product_data,
    )

    logger.info(f"Product {product_data.get('name')} has been removed from catalog")


async def handle_ai_description_generated(data: dict[str, Any]) -> None:
    """Handle ai.description.generated event."""
    event_data = data.get("data", {})
    logger.info(
        f"Handling ai.description.generated event for product {event_data.get('product_id')}"
    )

    # Send Telegram notification
    telegram_success = await telegram_service.send_event_notification(
        "ai.description.generated", event_data
    )
    await log_notification(
        "ai.description.generated", "telegram",
        "sent" if telegram_success else "failed",
        event_data,
    )


# Event handler mapping
EVENT_HANDLERS = {
    "user.created": handle_user_created,
    "user.updated": handle_user_updated,
    "user.deleted": handle_user_deleted,
    "product.created": handle_product_created,
    "product.updated": handle_product_updated,
    "product.deleted": handle_product_deleted,
    "ai.description.generated": handle_ai_description_generated,
}
