"""Product repository port (abstract interface).

Concrete implementation: infrastructure/persistence/repositories.py -> SQLAlchemyProductRepository
"""

from abc import ABC, abstractmethod

from ..entities.product import Product


class ProductRepository(ABC):
    """Abstract interface for product persistence operations."""

    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    async def list_products(self, skip: int = 0, limit: int = 100, category: str | None = None) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    async def count(self, category: str | None = None) -> int:
        raise NotImplementedError

    @abstractmethod
    async def create(self, product: Product) -> Product:
        raise NotImplementedError

    @abstractmethod
    async def update(self, product: Product) -> Product:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, product_id: int) -> None:
        raise NotImplementedError
