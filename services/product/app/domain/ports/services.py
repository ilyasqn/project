"""External service ports (abstract interfaces).

LLMService — Concrete implementation: infrastructure/external/llm_adapter.py -> OpenAILLMAdapter
GenerationHistoryRepository — Concrete implementation: infrastructure/external/mongodb_adapter.py -> MongoGenerationHistoryRepository
"""

from abc import ABC, abstractmethod
from typing import Any

from ..entities.generation_record import GenerationRecord


class LLMService(ABC):
    """Abstract interface for LLM text generation (OpenAI, Anthropic, etc.)."""

    @abstractmethod
    async def generate_description(
        self,
        product_name: str,
        category: str | None = None,
        price: str | None = None,
    ) -> str:
        raise NotImplementedError


class GenerationHistoryRepository(ABC):
    """Abstract interface for storing LLM generation history in MongoDB."""

    @abstractmethod
    async def save(self, record: GenerationRecord) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_by_product_id(self, product_id: int) -> list[GenerationRecord]:
        raise NotImplementedError
