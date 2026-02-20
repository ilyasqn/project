"""Pydantic request schemas for Product Service."""

from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0)
    sku: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    category: str | None = None
    generate_description: bool = Field(
        default=False,
        description="Use AI to generate product description",
    )


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    category: str | None = None
    is_active: bool | None = None


class AIDescriptionRequest(BaseModel):
    product_name: str
    category: str | None = None
    keywords: list[str] | None = None
