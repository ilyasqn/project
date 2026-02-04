"""Notification services (email, SMS, etc.)."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmailService:
    """Email notification service (simulated)."""

    async def send_welcome_email(self, user_data: dict[str, Any]) -> bool:
        """Send welcome email to new user."""
        email = user_data.get("email")
        full_name = user_data.get("full_name", "User")

        # Simulate sending email
        logger.info(
            f"[EMAIL] Sending welcome email to {email}\n"
            f"  Subject: Welcome to our platform, {full_name}!\n"
            f"  Body: Thank you for joining us. We're excited to have you!"
        )

        return True

    async def send_user_update_notification(self, user_data: dict[str, Any]) -> bool:
        """Send notification about user profile update."""
        email = user_data.get("email")

        logger.info(
            f"[EMAIL] Sending profile update notification to {email}\n"
            f"  Subject: Your profile has been updated\n"
            f"  Body: Your profile information has been successfully updated."
        )

        return True

    async def send_account_deletion_confirmation(
        self, user_data: dict[str, Any]
    ) -> bool:
        """Send confirmation of account deletion."""
        email = user_data.get("email")

        logger.info(
            f"[EMAIL] Sending account deletion confirmation to {email}\n"
            f"  Subject: Account deleted\n"
            f"  Body: Your account has been successfully deleted. We're sorry to see you go."
        )

        return True

    async def send_new_product_notification(self, product_data: dict[str, Any]) -> bool:
        """Send notification about new product (to admins/subscribers)."""
        product_name = product_data.get("name")
        product_id = product_data.get("id")

        logger.info(
            f"[EMAIL] Sending new product notification\n"
            f"  Subject: New product added: {product_name}\n"
            f"  Body: A new product (ID: {product_id}) has been added to the catalog."
        )

        return True

    async def send_product_update_notification(
        self, product_data: dict[str, Any]
    ) -> bool:
        """Send notification about product update."""
        product_name = product_data.get("name")
        product_id = product_data.get("id")

        logger.info(
            f"[EMAIL] Sending product update notification\n"
            f"  Subject: Product updated: {product_name}\n"
            f"  Body: Product (ID: {product_id}) has been updated."
        )

        return True


class SMSService:
    """SMS notification service (simulated)."""

    async def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS message."""
        logger.info(f"[SMS] Sending to {phone}: {message}")
        return True


class PushNotificationService:
    """Push notification service (simulated)."""

    async def send_push(self, user_id: int, title: str, body: str) -> bool:
        """Send push notification."""
        logger.info(f"[PUSH] Sending to user {user_id}: {title} - {body}")
        return True


# Singleton instances
email_service = EmailService()
sms_service = SMSService()
push_service = PushNotificationService()
