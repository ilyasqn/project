"""Pydantic schemas for Product Service."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Base schema for product data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0)
    sku: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    category: str | None = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    generate_description: bool = Field(
        default=False,
        description="Use AI to generate product description",
    )


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    category: str | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    """Schema for product response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    """Schema for list of products."""

    products: list[ProductResponse]
    total: int


class AIDescriptionRequest(BaseModel):
    """Schema for AI description generation request."""

    product_name: str
    category: str | None = None
    keywords: list[str] | None = None
