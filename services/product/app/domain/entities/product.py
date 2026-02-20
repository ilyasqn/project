"""Product domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Product:
    id: int | None = None
    name: str = ""
    description: str | None = None
    price: Decimal = Decimal("0.00")
    sku: str = ""
    stock_quantity: int = 0
    category: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
