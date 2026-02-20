"""Email notification adapter using SMTP.

Sends real emails via SMTP when configured (SMTP_HOST is set).
Falls back to logging when SMTP is not configured (development mode).

Configuration via DI container:
    smtp_host: SMTP server hostname (e.g., "smtp.gmail.com")
    smtp_port: SMTP server port (default: 587 for TLS)
    smtp_user: SMTP login username
    smtp_password: SMTP login password
    from_email: Sender email address
"""

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ...domain.ports.services import EmailNotificationService

logger = logging.getLogger(__name__)


class EmailServiceAdapter(EmailNotificationService):
    """Sends notification emails via SMTP.

    When smtp_host is empty, operates in dev mode (logs only, no actual send).
    """

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_email: str = "noreply@microservices.local",
    ):
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._password = smtp_password
        self._from_email = from_email
        self._configured = bool(smtp_host)

        if not self._configured:
            logger.warning(
                "SMTP not configured (SMTP_HOST is empty). "
                "Emails will be logged but not sent."
            )

    async def _send_email(self, to: str, subject: str, body: str) -> bool:
        if not self._configured:
            logger.info(
                f"[EMAIL-DEV] To: {to} | Subject: {subject} | Body: {body[:200]}"
            )
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self._from_email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._smtp_send, to, msg)
            logger.info(f"[EMAIL] Sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send to {to}: {e}")
            return False

    def _smtp_send(self, to: str, msg: MIMEMultipart) -> None:
        with smtplib.SMTP(self._host, self._port) as server:
            server.starttls()
            if self._user and self._password:
                server.login(self._user, self._password)
            server.send_message(msg, self._from_email, [to])

    async def send_welcome_email(self, user_data: dict[str, Any]) -> bool:
        email = user_data.get("email", "")
        full_name = user_data.get("full_name", "User")
        return await self._send_email(
            to=email,
            subject=f"Welcome to our platform, {full_name}!",
            body=(
                f"<h2>Welcome, {full_name}!</h2>"
                f"<p>Thank you for joining us. Your account is ready to use.</p>"
            ),
        )

    async def send_user_update_notification(self, user_data: dict[str, Any]) -> bool:
        email = user_data.get("email", "")
        return await self._send_email(
            to=email,
            subject="Your profile has been updated",
            body=(
                "<h2>Profile Updated</h2>"
                "<p>Your profile information has been successfully updated.</p>"
            ),
        )

    async def send_account_deletion_confirmation(self, user_data: dict[str, Any]) -> bool:
        email = user_data.get("email", "")
        return await self._send_email(
            to=email,
            subject="Account deleted",
            body=(
                "<h2>Account Deleted</h2>"
                "<p>Your account has been successfully deleted. "
                "We're sorry to see you go.</p>"
            ),
        )

    async def send_new_product_notification(self, product_data: dict[str, Any]) -> bool:
        product_name = product_data.get("name", "Unknown")
        product_id = product_data.get("id")
        admin_email = self._from_email
        return await self._send_email(
            to=admin_email,
            subject=f"New product added: {product_name}",
            body=(
                f"<h2>New Product</h2>"
                f"<p>Product <strong>{product_name}</strong> (ID: {product_id}) "
                f"has been added to the catalog.</p>"
            ),
        )

    async def send_product_update_notification(self, product_data: dict[str, Any]) -> bool:
        product_name = product_data.get("name", "Unknown")
        product_id = product_data.get("id")
        admin_email = self._from_email
        return await self._send_email(
            to=admin_email,
            subject=f"Product updated: {product_name}",
            body=(
                f"<h2>Product Updated</h2>"
                f"<p>Product <strong>{product_name}</strong> (ID: {product_id}) "
                f"has been updated.</p>"
            ),
        )
