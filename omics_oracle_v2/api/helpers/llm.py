"""
Simple LLM helper for API endpoints.

Provides lightweight OpenAI GPT integration without heavy abstractions.
"""

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


def call_openai(
    prompt: str,
    system_message: str = "You are a helpful genomics data analysis assistant.",
    api_key: Optional[str] = None,
    model: str = "gpt-4",
    max_tokens: int = 800,
    temperature: float = 0.7,
    timeout: int = 30,
) -> Optional[str]:
    """
    Call OpenAI API with a prompt.

    Args:
        prompt: User prompt
        system_message: System role message
        api_key: OpenAI API key (required)
        model: Model to use (default: gpt-4)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-1)
        timeout: Request timeout in seconds

    Returns:
        Generated text or None if call fails
    """
    if not HAS_OPENAI:
        logger.error("OpenAI library not installed")
        return None

    if not api_key:
        logger.error("OpenAI API key not provided")
        return None

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
        return content.strip() if content and content.strip() else None

    except Exception as e:
        error_msg = str(e)
        
        # Special handling for context length exceeded
        if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
            logger.error(
                f"OpenAI context length exceeded: {e}\n"
                f"Model: {model}, Max tokens requested: {max_tokens}\n"
                f"Suggestion: Reduce max_papers_per_dataset or use gpt-4-turbo model"
            )
        else:
            logger.error(f"OpenAI API call failed: {e}")
        
        return None
