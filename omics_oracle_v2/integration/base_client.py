"""
Base API client with common functionality.

Handles:
- HTTP communication
- Authentication
- Caching
- Rate limiting
- Error handling
- Retries
- API versioning
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Literal, Optional

import httpx

from .models import ErrorResponse

logger = logging.getLogger(__name__)


class APIClient:
    """
    Base client for all OmicsOracle API interactions.

    Features:
    - Automatic retry with exponential backoff
    - Response caching
    - Rate limiting
    - Authentication support
    - API versioning
    - Comprehensive error handling

    Usage:
        client = APIClient(
            base_url="http://localhost:8000",
            api_version="v1",
            timeout=30.0
        )

        response = await client.get("/health")
        data = await client.post("/search", json={"query": "CRISPR"})
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_version: str = "v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        cache_ttl: int = 300,  # 5 minutes
        api_key: Optional[str] = None,
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the API
            api_version: API version to use (v1, v2, etc.)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            cache_ttl: Cache TTL in seconds
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self.api_key = api_key

        # Simple in-memory cache (can be swapped with Redis)
        self._cache: Dict[str, tuple[Any, datetime]] = {}

        # Rate limiting (requests per minute)
        self._rate_limit = 60
        self._rate_window: list[datetime] = []

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = {
                "User-Agent": "OmicsOracle-Integration-Layer/2.0.0",
                "Accept": "application/json",
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
            )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_url(self, endpoint: str) -> str:
        """Build full URL with API version."""
        endpoint = endpoint.lstrip("/")
        return f"/api/{self.api_version}/{endpoint}"

    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Remove old requests
        self._rate_window = [t for t in self._rate_window if t > cutoff]

        if len(self._rate_window) >= self._rate_limit:
            raise Exception("Rate limit exceeded. Please wait before making more requests.")

        self._rate_window.append(now)

    def _get_cache_key(self, method: str, url: str, **kwargs) -> str:
        """Generate cache key."""
        # Simple cache key (can be enhanced)
        params = kwargs.get("params", {})
        json_data = kwargs.get("json", {})
        return f"{method}:{url}:{hash(str(params))}:{hash(str(json_data))}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.utcnow() < expires_at:
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                # Expired
                del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """Set cache value with TTL."""
        expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)
        self._cache[key] = (value, expires_at)
        logger.debug(f"Cache set: {key}")

    async def _request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        endpoint: str,
        use_cache: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            use_cache: Whether to use caching
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON as dictionary

        Raises:
            Exception: On API error or network failure
        """
        await self._ensure_client()

        url = self._build_url(endpoint)
        cache_key = self._get_cache_key(method, url, **kwargs)

        # Check cache for GET requests
        if method == "GET" and use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        # Check rate limit
        self._check_rate_limit()

        # Retry loop
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{method} {url} (attempt {attempt + 1}/{self.max_retries})")

                response = await self._client.request(method, url, **kwargs)

                # Handle errors
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error = ErrorResponse(
                        error=f"HTTP_{response.status_code}",
                        message=error_data.get("detail", response.reason_phrase),
                        details=error_data,
                    )
                    logger.error(f"API error: {error.message}")

                    # Don't retry client errors (4xx)
                    if 400 <= response.status_code < 500:
                        raise Exception(error.message)

                    # Retry server errors (5xx)
                    last_exception = Exception(error.message)
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue

                # Success
                result = response.json()

                # Cache GET requests
                if method == "GET" and use_cache:
                    self._set_cache(cache_key, result)

                return result

            except httpx.HTTPError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                last_exception = e

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        # All retries failed
        raise Exception(f"Request failed after {self.max_retries} attempts: {last_exception}")

    async def get(self, endpoint: str, use_cache: bool = True, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        return await self._request("GET", endpoint, use_cache=use_cache, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        return await self._request("POST", endpoint, use_cache=False, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request."""
        return await self._request("PUT", endpoint, use_cache=False, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._request("DELETE", endpoint, use_cache=False, **kwargs)

    async def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make PATCH request."""
        return await self._request("PATCH", endpoint, use_cache=False, **kwargs)

    async def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        return await self.get("/health", use_cache=False)

    def clear_cache(self):
        """Clear all cached responses."""
        self._cache.clear()
        logger.info("Cache cleared")
