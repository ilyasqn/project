"""Pytest fixtures for AI Service tests."""

import sys
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    mock = MagicMock()
    mock.generate = AsyncMock(
        return_value="A high-quality product designed for excellence."
    )
    mock.summarize = AsyncMock(return_value="Summary of the text.")
    mock.analyze = AsyncMock(
        return_value={"sentiment": "positive", "confidence": 0.9}
    )
    return mock


@pytest.fixture
def sample_product_created_event():
    """Sample product.created event data."""
    return {
        "event_type": "product.created",
        "data": {
            "id": 1,
            "name": "Test Product",
            "description": None,
            "price": "99.99",
            "sku": "TEST-001",
            "category": "Electronics",
            "is_active": True,
        },
    }


@pytest.fixture
def sample_product_with_description_event():
    """Sample product.created event with existing description."""
    return {
        "event_type": "product.created",
        "data": {
            "id": 2,
            "name": "Test Product 2",
            "description": "Existing description",
            "price": "149.99",
            "sku": "TEST-002",
            "category": "Books",
            "is_active": True,
        },
    }
