"""
Caching utilities for GEO data.

Provides simple file-based caching with TTL support for GEO metadata
and search results to reduce API calls and improve performance.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple file-based cache with TTL support.

    Uses JSON files for storage with MD5 hashing for safe filenames.
    Not intended for security-critical data.
    """

    def __init__(self, cache_dir: Path, default_ttl: int = 3600):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Cache initialized at {cache_dir} with TTL={default_ttl}s")

    def _get_cache_path(self, key: str) -> Path:
        """
        Get cache file path for a key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Use MD5 hash for safe filename (non-security use)
        key_hash = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()  # nosec B324
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached data if valid and not expired.

        Args:
            key: Cache key
            ttl: Time-to-live override (uses default if None)

        Returns:
            Cached data or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {key}")
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            max_age = ttl if ttl is not None else self.default_ttl
            age = time.time() - cache_data.get("timestamp", 0)

            if age > max_age:
                # Cache expired, remove it
                logger.debug(f"Cache expired: {key} (age={age:.0f}s, max={max_age}s)")
                cache_path.unlink(missing_ok=True)
                return None

            logger.debug(f"Cache hit: {key} (age={age:.0f}s)")
            return cache_data.get("data")

        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Cache data with timestamp.

        Args:
            key: Cache key
            data: Data to cache (must be JSON-serializable)
        """
        cache_path = self._get_cache_path(key)

        cache_data = {"timestamp": time.time(), "data": data}

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=True, indent=2)
            logger.debug(f"Cached: {key}")
        except (OSError, TypeError) as e:
            logger.warning(f"Failed to cache data for {key}: {e}")

    def delete(self, key: str) -> bool:
        """
        Delete cached data.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache: {key}")
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError as e:
                logger.warning(f"Failed to delete {cache_file}: {e}")

        logger.info(f"Cleared {count} cache files")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_directory": str(self.cache_dir),
            "default_ttl": self.default_ttl,
        }
