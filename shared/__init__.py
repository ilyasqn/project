"""Shared utilities for microservices."""

from .rabbitmq import RabbitMQClient, get_rabbitmq_client

__all__ = ["RabbitMQClient", "get_rabbitmq_client"]
