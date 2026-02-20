"""Generation record domain entity for LLM history."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GenerationRecord:
    id: str | None = None
    product_id: int = 0
    product_name: str = ""
    prompt: str = ""
    description: str = ""
    tokens_used: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
