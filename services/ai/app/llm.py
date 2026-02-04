"""LLM client for AI Service."""

import logging
import os
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")


class LLMClient:
    """OpenAI-compatible LLM client."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY or "dummy-key",
            base_url=OPENAI_BASE_URL,
        )
        self.model = DEFAULT_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Return a fallback response for demo purposes
            if "product description" in prompt.lower():
                return "A high-quality product designed to meet your needs. Features excellent craftsmanship and reliable performance."
            return f"[Demo mode] Generated response for: {prompt[:50]}..."

    async def summarize(
        self,
        text: str,
        max_length: int = 100,
    ) -> str:
        """
        Summarize text.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary

        Returns:
            Summarized text
        """
        prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}"

        return await self.generate(
            prompt=prompt,
            system_prompt="You are a helpful assistant that creates concise summaries.",
            max_tokens=max_length * 2,
            temperature=0.3,
        )

    async def analyze(
        self,
        text: str,
        analysis_type: str = "sentiment",
    ) -> dict[str, Any]:
        """
        Analyze text.

        Args:
            text: Text to analyze
            analysis_type: Type of analysis (sentiment, keywords, entities)

        Returns:
            Analysis results
        """
        prompts = {
            "sentiment": f"Analyze the sentiment of the following text. Respond with JSON containing 'sentiment' (positive/negative/neutral) and 'confidence' (0-1):\n\n{text}",
            "keywords": f"Extract key topics and keywords from the following text. Respond with JSON containing 'keywords' (list of strings):\n\n{text}",
            "entities": f"Extract named entities from the following text. Respond with JSON containing 'entities' (list of objects with 'name' and 'type'):\n\n{text}",
        }

        prompt = prompts.get(
            analysis_type,
            f"Analyze the following text:\n\n{text}",
        )

        result = await self.generate(
            prompt=prompt,
            system_prompt="You are a helpful assistant that analyzes text. Always respond with valid JSON.",
            max_tokens=300,
            temperature=0.2,
        )

        # Try to parse as JSON, return raw result if fails
        try:
            import json

            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_result": result, "analysis_type": analysis_type}


# Singleton instance
llm_client = LLMClient()
