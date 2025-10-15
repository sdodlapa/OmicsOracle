"""
Async LLM client for high-performance concurrent operations.

Provides async/await versions of LLM operations with:
- Concurrent batch processing
- Rate limiting
- Connection pooling
- Automatic retries
"""

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

logger = logging.getLogger(__name__)


class AsyncLLMClient:
    """
    Async LLM client for concurrent operations.

    Features:
    - Async/await API for non-blocking operations
    - Batch processing with concurrency control
    - Rate limiting
    - Response caching
    - Connection pooling

    Example:
        >>> client = AsyncLLMClient(provider="openai")
        >>> response = await client.generate("Summarize...")
        >>> responses = await client.generate_batch(prompts, max_concurrent=10)
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 3,
        rate_limit_per_minute: int = 60,
    ):
        """
        Initialize async LLM client.

        Args:
            provider: LLM provider ("openai", "anthropic")
            model: Model name
            cache_enabled: Enable response caching
            cache_dir: Cache directory
            temperature: Sampling temperature
            max_retries: Max retry attempts
            rate_limit_per_minute: Max requests per minute
        """
        self.provider = provider.lower()
        self.temperature = temperature
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.rate_limit = rate_limit_per_minute

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

        # Rate limiting
        self.semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        self.request_times = []

        # Initialize provider client
        self._init_provider()

        # Track usage
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"Async LLM client initialized: {provider}/{model}")

    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-5-sonnet-20241022",
        }
        return defaults.get(self.provider, "gpt-4-turbo-preview")

    def _init_provider(self):
        """Initialize provider-specific async client."""
        try:
            if self.provider == "openai":
                from openai import AsyncOpenAI

                self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            elif self.provider == "anthropic":
                import anthropic

                self.client = anthropic.AsyncAnthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except ImportError as e:
            logger.error(f"Failed to import {self.provider} async library: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Generate LLM response asynchronously.

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
            cached = await self._get_cached(cache_key)
            if cached:
                self.cache_hits += 1
                logger.debug(f"Cache hit for prompt (key: {cache_key[:8]}...)")
                return {"content": cached, "tokens": 0, "cached": True}

        self.cache_misses += 1

        # Rate limiting
        await self._wait_for_rate_limit()

        # Generate with retry logic
        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:
                    if self.provider == "openai":
                        response = await self._openai_generate(
                            prompt, system_prompt, response_format, max_tokens
                        )
                    elif self.provider == "anthropic":
                        response = await self._anthropic_generate(
                            prompt, system_prompt, max_tokens
                        )
                    else:
                        raise ValueError(f"Unknown provider: {self.provider}")

                # Cache response
                if self.cache_enabled:
                    await self._cache_response(cache_key, response["content"])

                self.total_tokens += response.get("tokens", 0)
                return response

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {e}")
                    raise

    async def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        max_concurrent: int = 10,
        response_format: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> List[Dict[str, Any]]:
        """
        Generate responses for multiple prompts concurrently.

        Args:
            prompts: List of prompts
            system_prompt: System prompt (same for all)
            max_concurrent: Max concurrent requests
            response_format: "json" for structured output
            max_tokens: Maximum tokens per response

        Returns:
            List of response dicts
        """
        tasks = [
            self.generate(prompt, system_prompt, response_format, max_tokens)
            for prompt in prompts
        ]

        # Process in batches to control concurrency
        results = []
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i : i + max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)

        # Handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch item {i} failed: {result}")
                results[i] = {
                    "content": "",
                    "tokens": 0,
                    "cached": False,
                    "error": str(result),
                }

        return results

    async def generate_json(
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
        response = await self.generate(
            prompt, system_prompt, response_format="json", max_tokens=max_tokens
        )

        try:
            return json.loads(response["content"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response: {response['content']}")
            raise

    async def _openai_generate(
        self,
        prompt: str,
        system_prompt: Optional[str],
        response_format: Optional[str],
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Generate response using OpenAI async API."""
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

        response = await self.client.chat.completions.create(**kwargs)

        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens,
            "cached": False,
        }

    async def _anthropic_generate(
        self, prompt: str, system_prompt: Optional[str], max_tokens: int
    ) -> Dict[str, Any]:
        """Generate response using Anthropic async API."""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)

        return {
            "content": response.content[0].text,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
            "cached": False,
        }

    async def _wait_for_rate_limit(self):
        """Wait if rate limit would be exceeded."""
        import time

        current_time = time.time()

        # Remove old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if current_time - t < 60]

        # Check if we're at the limit
        if len(self.request_times) >= self.rate_limit:
            # Wait until oldest request is more than 60 seconds old
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                current_time = time.time()
                self.request_times = [
                    t for t in self.request_times if current_time - t < 60
                ]

        # Record this request
        self.request_times.append(current_time)

    def _get_cache_key(
        self, prompt: str, system_prompt: Optional[str], response_format: Optional[str]
    ) -> str:
        """Generate cache key from inputs."""
        content = f"{self.model}:{system_prompt or ''}:{prompt}:{response_format or ''}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def _get_cached(self, cache_key: str) -> Optional[str]:
        """Get cached response asynchronously."""
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                return data.get("response")
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
                return None

        return None

    async def _cache_response(self, cache_key: str, response: str):
        """Cache response asynchronously."""
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            async with aiofiles.open(cache_file, "w") as f:
                content = json.dumps({"response": response, "model": self.model})
                await f.write(content)
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


# Convenience function for scoring publication relevance
async def score_publication_relevance_async(
    llm_client: AsyncLLMClient, query: str, publication: Any
) -> float:
    """
    Score publication relevance asynchronously.

    Args:
        llm_client: Async LLM client
        query: Search query
        publication: Publication object

    Returns:
        Relevance score (0.0-1.0)
    """
    system_prompt = """You are a biomedical research expert. Score the relevance of a publication to a research query.

    Return ONLY a JSON object with this format:
    {
        "score": 0.85,
        "reasoning": "brief explanation"
    }

    Score from 0.0 (not relevant) to 1.0 (highly relevant).
    """

    user_prompt = f"""
    Query: {query}

    Publication:
    Title: {publication.title}
    Abstract: {publication.abstract[:500] if publication.abstract else 'N/A'}

    Score this publication's relevance to the query.
    """

    try:
        response = await llm_client.generate_json(
            user_prompt, system_prompt, max_tokens=500
        )
        return float(response.get("score", 0.5))
    except Exception as e:
        logger.error(f"Failed to score publication: {e}")
        return 0.5  # Default middle score on error


async def score_publications_batch_async(
    llm_client: AsyncLLMClient,
    query: str,
    publications: List[Any],
    max_concurrent: int = 10,
) -> List[float]:
    """
    Score multiple publications concurrently.

    Args:
        llm_client: Async LLM client
        query: Search query
        publications: List of publications
        max_concurrent: Max concurrent scoring operations

    Returns:
        List of relevance scores
    """
    tasks = [
        score_publication_relevance_async(llm_client, query, pub)
        for pub in publications
    ]

    scores = []
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i : i + max_concurrent]
        batch_scores = await asyncio.gather(*batch, return_exceptions=True)

        # Handle exceptions
        for score in batch_scores:
            if isinstance(score, Exception):
                logger.error(f"Scoring failed: {score}")
                scores.append(0.5)
            else:
                scores.append(score)

    return scores
