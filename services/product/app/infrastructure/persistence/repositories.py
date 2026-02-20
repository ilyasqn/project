"""SQLAlchemy implementation of ProductRepository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.product import Product
from ...domain.ports.repositories import ProductRepository
from .models import ProductModel


class SQLAlchemyProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            description=model.description,
            price=model.price,
            sku=model.sku,
            stock_quantity=model.stock_quantity,
            category=model.category,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.sku == sku)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_products(self, skip: int = 0, limit: int = 100, category: str | None = None) -> list[Product]:
        query = select(ProductModel)
        if category:
            query = query.where(ProductModel.category == category)
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def count(self, category: str | None = None) -> int:
        query = select(func.count()).select_from(ProductModel)
        if category:
            query = query.where(ProductModel.category == category)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def create(self, product: Product) -> Product:
        model = ProductModel(
            name=product.name,
            description=product.description,
            price=product.price,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            category=product.category,
            is_active=product.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, product: Product) -> Product:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product.id)
        )
        model = result.scalar_one()
        model.name = product.name
        model.description = product.description
        model.price = product.price
        model.sku = product.sku
        model.stock_quantity = product.stock_quantity
        model.category = product.category
        model.is_active = product.is_active
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, product_id: int) -> None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()
