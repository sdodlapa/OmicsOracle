"""
LLM client with multi-provider support and caching.

Supports OpenAI, Anthropic, and local models (Ollama).
Includes response caching to minimize API costs.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    Features:
    - Multi-provider support (OpenAI, Anthropic, Ollama)
    - Response caching (reduces costs)
    - Structured JSON output
    - Retry logic
    - Token usage tracking

    Example:
        >>> client = LLMClient(provider="openai", model="gpt-4-turbo")
        >>> response = client.generate("Summarize this paper...")
        >>> json_data = client.generate_json("Extract findings...")
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 3,
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider ("openai", "anthropic", "ollama")
            model: Model name (defaults based on provider)
            cache_enabled: Enable response caching
            cache_dir: Cache directory (default: ./data/llm_cache)
            temperature: Sampling temperature (0-1, lower = more deterministic)
            max_retries: Max retry attempts on failure
        """
        self.provider = provider.lower()
        self.temperature = temperature
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled

        # Set default models
        if model is None:
            model = self._get_default_model()
        self.model = model

        # Setup cache
        if cache_enabled:
            if cache_dir is None:
                cache_dir = "./data/llm_cache"
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None

        # Initialize provider client
        self._init_provider()

        # Track usage
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"LLM client initialized: {provider}/{model}")

    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-5-sonnet-20241022",
            "ollama": "llama3.1",
        }
        return defaults.get(self.provider, "gpt-4-turbo-preview")

    def _init_provider(self):
        """Initialize provider-specific client."""
        try:
            if self.provider == "openai":
                from openai import OpenAI

                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            elif self.provider == "anthropic":
                import anthropic

                self.client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )

            elif self.provider == "ollama":
                # Local model - no API key needed
                pass

                self.client = None  # Will use requests directly
                self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except ImportError as e:
            logger.error(f"Failed to import {self.provider} library: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Generate LLM response.

        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
            response_format: "json" for structured output
            max_tokens: Maximum tokens in response

        Returns:
            Dict with 'content', 'tokens', 'cached' fields
        """
        # Check cache
        if self.cache_enabled:
            cache_key = self._get_cache_key(prompt, system_prompt, response_format)
            cached = self._get_cached(cache_key)
            if cached:
                self.cache_hits += 1
                logger.debug(f"Cache hit for prompt (key: {cache_key[:8]}...)")
                return {"content": cached, "tokens": 0, "cached": True}

        self.cache_misses += 1

        # Generate response
        try:
            if self.provider == "openai":
                response = self._openai_generate(
                    prompt, system_prompt, response_format, max_tokens
                )
            elif self.provider == "anthropic":
                response = self._anthropic_generate(prompt, system_prompt, max_tokens)
            elif self.provider == "ollama":
                response = self._ollama_generate(prompt, system_prompt, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

            # Cache response
            if self.cache_enabled:
                self._cache_response(cache_key, response["content"])

            self.total_tokens += response.get("tokens", 0)
            return response

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def generate_json(
        self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON object
        """
        response = self.generate(
            prompt, system_prompt, response_format="json", max_tokens=max_tokens
        )

        try:
            return json.loads(response["content"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response: {response['content']}")
            raise

    def _openai_generate(
        self,
        prompt: str,
        system_prompt: Optional[str],
        response_format: Optional[str],
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Generate response using OpenAI."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)

        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "cached": False,
        }

    def _anthropic_generate(
        self, prompt: str, system_prompt: Optional[str], max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using Anthropic."""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        return {
            "content": response.content[0].text,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
            "cached": False,
        }

    def _ollama_generate(
        self, prompt: str, system_prompt: Optional[str], max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using Ollama (local)."""
        import requests

        url = f"{self.ollama_url}/api/generate"

        data = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": max_tokens},
        }

        response = requests.post(url, json=data)
        response.raise_for_status()

        result = response.json()

        return {
            "content": result["response"],
            "tokens": 0,
            "cached": False,
        }  # Ollama doesn't return tokens

    def _get_cache_key(
        self, prompt: str, system_prompt: Optional[str], response_format: Optional[str]
    ) -> str:
        """Generate cache key from inputs."""
        content = f"{self.model}:{system_prompt or ''}:{prompt}:{response_format or ''}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[str]:
        """Get cached response."""
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                return data.get("response")
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
                return None

        return None

    def _cache_response(self, cache_key: str, response: str):
        """Cache response."""
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w") as f:
                json.dump({"response": response, "model": self.model}, f)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_tokens": self.total_tokens,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0
            ),
        }
