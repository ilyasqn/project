"""Event handlers for processing RabbitMQ messages in AI Service."""

import logging
from typing import Any

from .events import publish_ai_event
from .llm import llm_client
from .mongodb import save_generation_history
from .redis_cache import cache_description, get_cached_description

logger = logging.getLogger(__name__)


async def handle_product_created(data: dict[str, Any]) -> None:
    """
    Handle product.created event.

    Generates a description for the product if one doesn't exist.
    """
    product = data.get("data", {})
    product_id = product.get("id")
    product_name = product.get("name")

    if not product_id or not product_name:
        logger.warning(f"Invalid product data in event: {data}")
        return

    logger.info(f"Handling product.created event for product {product_id}")

    # Skip if description already exists
    if product.get("description"):
        logger.info(f"Product {product_id} already has a description, skipping")
        return

    # Check Redis cache first
    cached_description = await get_cached_description(product_id)
    if cached_description:
        logger.info(f"Using cached description for product {product_id}")
        await publish_ai_event("description.generated", {
            "product_id": product_id,
            "description": cached_description,
            "cached": True,
        })
        return

    # Generate description with LLM
    category = product.get("category", "general")
    price = product.get("price")

    prompt = f"Generate a compelling product description for: {product_name}"
    if category:
        prompt += f", category: {category}"
    if price:
        prompt += f", price: ${price}"
    prompt += ". Keep it concise (2-3 sentences) and highlight key benefits."

    try:
        description = await llm_client.generate(
            prompt=prompt,
            system_prompt="You are a professional copywriter creating product descriptions. Be concise and engaging.",
            max_tokens=150,
            temperature=0.7,
        )

        # Cache the description in Redis (24h TTL)
        await cache_description(product_id, description)

        # Save to MongoDB for history
        await save_generation_history(
            product_id=product_id,
            product_name=product_name,
            prompt=prompt,
            description=description,
        )

        # Publish event with generated description
        await publish_ai_event("description.generated", {
            "product_id": product_id,
            "description": description,
            "cached": False,
        })

        logger.info(f"Generated and published description for product {product_id}")

    except Exception as e:
        logger.error(f"Error generating description for product {product_id}: {e}")


# Event handler mapping
EVENT_HANDLERS = {
    "product.created": handle_product_created,
}
