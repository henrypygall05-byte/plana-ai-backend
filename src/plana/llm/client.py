"""
LLM client abstraction.

Provides a unified interface for different LLM providers.
"""

from typing import Literal

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from plana.config import get_settings

logger = structlog.get_logger(__name__)


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    Currently supports:
    - Anthropic Claude
    - OpenAI GPT
    """

    def __init__(
        self,
        provider: Literal["anthropic", "openai"] | None = None,
    ):
        """Initialize LLM client.

        Args:
            provider: LLM provider to use (defaults to settings)
        """
        self.settings = get_settings()
        self.provider = provider or self.settings.llm.provider
        self._client = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the client is initialized."""
        if self._initialized:
            return

        if self.provider == "anthropic":
            import anthropic

            api_key = self.settings.llm.anthropic_api_key
            if not api_key:
                raise ValueError("Anthropic API key not configured")
            self._client = anthropic.AsyncAnthropic(
                api_key=api_key.get_secret_value()
            )

        elif self.provider == "openai":
            import openai

            api_key = self.settings.llm.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            self._client = openai.AsyncOpenAI(
                api_key=api_key.get_secret_value()
            )

        self._initialized = True
        logger.info("LLM client initialized", provider=self.provider)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature

        Returns:
            Generated text
        """
        await self._ensure_initialized()

        max_tokens = max_tokens or self.settings.llm.max_tokens
        temperature = temperature if temperature is not None else self.settings.llm.temperature

        if self.provider == "anthropic":
            return await self._generate_anthropic(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            return await self._generate_openai(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using Anthropic Claude."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.settings.llm.anthropic_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self._client.messages.create(**kwargs)

        return response.content[0].text

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Generate using OpenAI GPT."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.settings.llm.openai_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content

    async def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        if self.provider == "anthropic":
            await self._ensure_initialized()
            result = await self._client.count_tokens(text)
            return result
        else:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.settings.llm.openai_model)
            return len(encoding.encode(text))
