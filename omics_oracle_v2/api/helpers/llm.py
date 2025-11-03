"""
Simple LLM helper for API endpoints.

Provides lightweight OpenAI GPT integration without heavy abstractions.
Includes Redis caching to avoid redundant expensive API calls.
"""

import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Optional OpenAI dependency
try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI library not available")


async def call_openai(
    prompt: str,
    system_message: str = "You are a helpful genomics data analysis assistant.",
    api_key: Optional[str] = None,
    model: str = "gpt-4",
    max_tokens: int = 800,
    temperature: float = 0.7,
    timeout: int = 30,
) -> Optional[str]:
    """
    Call OpenAI GPT API with Redis caching to avoid redundant expensive calls.

    Cache strategy:
    - Key: Hash of (prompt + system_message + model + temperature)
    - TTL: 7 days (604800 seconds)
    - Hit: Return cached response (~0.1s, $0 cost)
    - Miss: Call OpenAI API (~5-8s, $0.03-0.10 cost), then cache

    Args:
        prompt: User prompt for the LLM
        system_message: System instructions for the LLM behavior
        api_key: OpenAI API key
        model: OpenAI model name (gpt-4, gpt-4-turbo, etc.)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-2.0)
        timeout: API request timeout in seconds

    Returns:
        Generated text response or None if failed
    """
    if not HAS_OPENAI:
        logger.error("OpenAI library not installed")
        return None

    if not api_key:
        logger.error("OpenAI API key not provided")
        return None

    # Generate cache key from prompt + config
    # Include temperature and model to avoid serving wrong cached response
    cache_input = f"{prompt}|{system_message}|{model}|{temperature}"
    cache_key = f"ai_summary:{hashlib.sha256(cache_input.encode()).hexdigest()[:16]}"

    # Try Redis cache first (hot-tier)
    try:
        from omics_oracle_v2.cache.redis_cache import RedisCache

        redis = RedisCache()

        # Check cache
        cached_response = await redis.get(cache_key)
        if cached_response:
            # Parse JSON if it's a string
            if isinstance(cached_response, str):
                try:
                    cached_data = json.loads(cached_response)
                    cached_text = cached_data.get("response", "")
                except json.JSONDecodeError:
                    # Old cache format - plain text
                    cached_text = cached_response
            else:
                cached_text = cached_response

            logger.info(
                f"[CACHE HIT] AI summary cache HIT (saved ~$0.05 + 6s) "
                f"[key={cache_key[:12]}...]"
            )
            return cached_text.strip() if cached_text and cached_text.strip() else None
        else:
            logger.info(
                f"[CACHE MISS] AI summary cache MISS, calling OpenAI API... [key={cache_key[:12]}...]"
            )

    except Exception as cache_error:
        logger.warning(f"Cache check failed: {cache_error}, proceeding with API call")

    # Cache miss or cache unavailable - call OpenAI
    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            logger.warning("OpenAI returned empty response")
            return None

        response_text = content.strip()

        # Save to cache for 7 days (604800 seconds)
        try:
            cache_data = json.dumps({"response": response_text, "model": model})
            await redis.set(cache_key, cache_data, ttl=604800)
            logger.info(
                f"[CACHED] Cached AI summary for 7 days [key={cache_key[:12]}...]"
            )
        except Exception as cache_save_error:
            logger.warning(f"Failed to cache AI response: {cache_save_error}")

        return response_text

    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}", exc_info=True)
        return None
