"""Pydantic response schemas for Product Service."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Decimal
    sku: str
    stock_quantity: int
    category: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int


class GenerationHistoryResponse(BaseModel):
    id: str | None
    product_id: int
    product_name: str
    prompt: str
    description: str
    tokens_used: int | None
    created_at: datetime | None
