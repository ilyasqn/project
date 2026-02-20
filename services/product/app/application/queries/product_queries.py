"""Product query definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetProductQuery:
    product_id: int


@dataclass(frozen=True)
class ListProductsQuery:
    skip: int = 0
    limit: int = 100
    category: str | None = None


@dataclass(frozen=True)
class GetGenerationHistoryQuery:
    product_id: int
