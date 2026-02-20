"""Unit of Work — manages a single database transaction."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories import SQLAlchemyProductRepository


class UnitOfWork:
    products: SQLAlchemyProductRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def __aenter__(self):
        self._session = self._session_factory()
        self.products = SQLAlchemyProductRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()
