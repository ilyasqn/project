"""OpenAI LLM adapter - implements LLMService port."""

import logging

from openai import AsyncOpenAI

from ...domain.ports.services import LLMService

logger = logging.getLogger(__name__)


class OpenAILLMAdapter(LLMService):
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=base_url,
        )
        self._model = model

    async def generate_description(
        self,
        product_name: str,
        category: str | None = None,
        price: str | None = None,
    ) -> str:
        prompt = f"Generate a compelling product description for: {product_name}"
        if category:
            prompt += f", category: {category}"
        if price:
            prompt += f", price: ${price}"
        prompt += ". Keep it concise (2-3 sentences) and highlight key benefits."

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional copywriter creating product descriptions. Be concise and engaging.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "A high-quality product designed to meet your needs. Features excellent craftsmanship and reliable performance."
