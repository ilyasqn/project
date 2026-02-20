"""Product command definitions."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CreateProductCommand:
    name: str
    price: Decimal
    sku: str
    description: str | None = None
    stock_quantity: int = 0
    category: str | None = None
    generate_description: bool = False


@dataclass(frozen=True)
class UpdateProductCommand:
    product_id: int
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None
    category: str | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class DeleteProductCommand:
    product_id: int


@dataclass(frozen=True)
class GenerateDescriptionCommand:
    product_name: str
    category: str | None = None
    keywords: list[str] | None = None
