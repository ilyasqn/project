"""Event handlers for processing RabbitMQ messages in Product Service."""

import logging
from typing import Any

from sqlalchemy import select

from .database import async_session_maker
from .events import publish_product_event
from .models import Product
from .redis_cache import invalidate_product_cache

logger = logging.getLogger(__name__)


async def handle_description_generated(data: dict[str, Any]) -> None:
    """
    Handle ai.description.generated event.

    Updates the product with the AI-generated description.
    """
    event_data = data.get("data", {})
    product_id = event_data.get("product_id")
    description = event_data.get("description")

    if not product_id or not description:
        logger.warning(f"Invalid data in ai.description.generated event: {data}")
        return

    logger.info(f"Handling ai.description.generated event for product {product_id}")

    async with async_session_maker() as session:
        # Get the product
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            logger.warning(f"Product {product_id} not found")
            return

        # Only update if product doesn't have a description yet
        if product.description:
            logger.info(f"Product {product_id} already has a description, skipping")
            return

        # Update the product with the AI-generated description
        product.description = description
        await session.commit()
        await session.refresh(product)

        logger.info(f"Updated product {product_id} with AI-generated description")

        # Invalidate product cache
        await invalidate_product_cache(product_id)

        # Publish product.updated event
        await publish_product_event("updated", product.to_dict())


# Event handler mapping
EVENT_HANDLERS = {
    "ai.description.generated": handle_description_generated,
}
