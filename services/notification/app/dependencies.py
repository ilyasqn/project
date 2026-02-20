"""Simple dependency factories for Notification Service."""

from .infrastructure.external.email_adapter import EmailServiceAdapter
from .infrastructure.external.mongodb_adapter import MongoNotificationLogRepository
from .infrastructure.external.telegram_adapter import TelegramServiceAdapter

_email_service = None
_telegram_service = None
_mongodb_database = None


def init(email_service, telegram_service, mongodb_database):
    global _email_service, _telegram_service, _mongodb_database
    _email_service = email_service
    _telegram_service = telegram_service
    _mongodb_database = mongodb_database


def get_email_service() -> EmailServiceAdapter:
    return _email_service


def get_telegram_service() -> TelegramServiceAdapter:
    return _telegram_service


def get_log_repo() -> MongoNotificationLogRepository:
    return MongoNotificationLogRepository(_mongodb_database)
