"""API routes for Product Service."""

import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .events import publish_product_event
from .models import Product
from .redis_cache import cache_product, get_cached_product, invalidate_product_cache
from .schemas import (
    AIDescriptionRequest,
    ProductCreate,
    ProductList,
    ProductResponse,
    ProductUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8004")


async def generate_ai_description(name: str, category: str | None = None) -> str | None:
    """Call AI service to generate product description."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/ai/generate",
                json={
                    "prompt": f"Write a compelling product description for: {name}"
                    + (f" in category: {category}" if category else ""),
                    "max_tokens": 200,
                },
                timeout=30.0,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("text")
    except Exception as e:
        logger.warning(f"Failed to generate AI description: {e}")
    return None


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Create a new product."""
    # Check if SKU already exists
    existing = await db.execute(select(Product).where(Product.sku == product.sku))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists",
        )

    description = product.description
    if product.generate_description and not description:
        description = await generate_ai_description(product.name, product.category)

    db_product = Product(
        name=product.name,
        description=description,
        price=product.price,
        sku=product.sku,
        stock_quantity=product.stock_quantity,
        category=product.category,
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    # Publish product.created event
    await publish_product_event("created", db_product.to_dict())

    return db_product


@router.get("/", response_model=ProductList)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all products."""
    query = select(Product)
    if category:
        query = query.where(Product.category == category)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    count_query = select(Product)
    if category:
        count_query = count_query.where(Product.category == category)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return ProductList(products=products, total=total)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get a product by ID."""
    # Check cache first
    cached = await get_cached_product(product_id)
    if cached:
        return cached

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Cache the product
    await cache_product(product_id, product.to_dict())

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, product_update: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    # Publish product.updated event
    await publish_product_event("updated", product.to_dict())

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product_data = product.to_dict()
    await db.delete(product)
    await db.commit()

    # Publish product.deleted event
    await publish_product_event("deleted", product_data)

    return None


@router.post("/generate-description")
async def generate_description(request: AIDescriptionRequest):
    """Generate AI description for a product."""
    description = await generate_ai_description(request.product_name, request.category)

    if not description:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable",
        )

    return {"description": description}
