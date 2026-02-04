"""API routes for AI Service."""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .events import publish_ai_event
from .llm import llm_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


class GenerateRequest(BaseModel):
    """Request schema for text generation."""

    prompt: str = Field(..., min_length=1)
    system_prompt: str | None = None
    max_tokens: int = Field(default=500, ge=1, le=4000)
    temperature: float = Field(default=0.7, ge=0, le=2)


class GenerateResponse(BaseModel):
    """Response schema for text generation."""

    text: str
    model: str
    tokens_used: int | None = None


class SummarizeRequest(BaseModel):
    """Request schema for text summarization."""

    text: str = Field(..., min_length=10)
    max_length: int = Field(default=100, ge=10, le=500)


class SummarizeResponse(BaseModel):
    """Response schema for text summarization."""

    summary: str
    original_length: int
    summary_length: int


class AnalyzeRequest(BaseModel):
    """Request schema for text analysis."""

    text: str = Field(..., min_length=10)
    analysis_type: Literal["sentiment", "keywords", "entities"] = "sentiment"


class AnalyzeResponse(BaseModel):
    """Response schema for text analysis."""

    analysis_type: str
    result: dict


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Generate text using LLM."""
    try:
        text = await llm_client.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Publish event
        await publish_ai_event(
            "generation.completed",
            {
                "prompt_length": len(request.prompt),
                "response_length": len(text),
            },
        )

        return GenerateResponse(
            text=text,
            model=llm_client.model,
        )

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """Summarize text using LLM."""
    try:
        summary = await llm_client.summarize(
            text=request.text,
            max_length=request.max_length,
        )

        return SummarizeResponse(
            summary=summary,
            original_length=len(request.text),
            summary_length=len(summary),
        )

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text using LLM."""
    try:
        result = await llm_client.analyze(
            text=request.text,
            analysis_type=request.analysis_type,
        )

        # Publish event
        await publish_ai_event(
            "analysis.completed",
            {
                "analysis_type": request.analysis_type,
                "text_length": len(request.text),
            },
        )

        return AnalyzeResponse(
            analysis_type=request.analysis_type,
            result=result,
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )
