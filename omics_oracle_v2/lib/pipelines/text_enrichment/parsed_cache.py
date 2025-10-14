"""
Parsed content cache manager for full-text extraction.

This module provides caching for parsed PDF/XML content to avoid expensive
re-parsing operations. Once a document is parsed, the structured content
(tables, figures, sections, etc.) is saved as JSON for instant future access.

Key Features:
- JSON-based storage (human-readable, debuggable)
- 90-day TTL (time-to-live) for cache freshness
- Automatic stale detection
- Compression for large documents
- Metadata tracking (parse time, quality score, etc.)

Performance:
- Parse time: ~2 seconds (first time)
- Cache hit: ~10ms (200x faster!)
- Storage: ~50KB per paper (compressed JSON)

Example:
    >>> from omics_oracle_v2.lib.enrichment.fulltext.parsed_cache import ParsedCache
    >>>
    >>> cache = ParsedCache()
    >>>
    >>> # Try to get cached content
    >>> cached = await cache.get(publication_id)
    >>> if cached:
    >>>     print(f"Cache hit! {len(cached['tables'])} tables")
    >>> else:
    >>>     # Parse and cache
    >>>     content = parse_pdf(pdf_path)
    >>>     await cache.save(publication_id, content)

Author: OmicsOracle Team
Date: October 11, 2025
"""

import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ParsedCache:
    """
    Cache manager for parsed full-text content.

    This class handles caching of parsed PDF/XML content to avoid
    expensive re-parsing operations. Content is stored as compressed
    JSON files with metadata for tracking freshness and quality.

    Cache Structure:
        data/fulltext/parsed/
        +-- {publication_id}.json       # Uncompressed (for debugging)
        +-- {publication_id}.json.gz    # Compressed (production)

    Cache Entry Format:
        {
            "publication_id": "PMC9876543",
            "cached_at": "2025-10-11T10:30:00Z",
            "source_file": "data/fulltext/pdf/pmc/PMC9876543.pdf",
            "source_type": "pdf",
            "parse_duration_ms": 2345,
            "quality_score": 0.95,
            "content": {
                "title": "Paper Title",
                "abstract": "Abstract text...",
                "sections": [...],
                "tables": [...],
                "figures": [...],
                "references": [...],
                "metadata": {...}
            }
        }

    Attributes:
        cache_dir: Directory for storing cached content
        ttl_days: Time-to-live in days (default: 90)
        use_compression: Whether to use gzip compression (default: True)
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl_days: int = 90, use_compression: bool = True):
        """
        Initialize ParsedCache.

        Args:
            cache_dir: Directory for cache storage.
                      Defaults to 'data/fulltext/parsed' in project root.
            ttl_days: Time-to-live in days before cache is considered stale.
            use_compression: Whether to use gzip compression (saves ~80% space).
        """
        if cache_dir is None:
            # Default to data/fulltext/parsed in project root
            cache_dir = Path(__file__).parent.parent.parent.parent / "data" / "fulltext" / "parsed"

        self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days
        self.use_compression = use_compression

        # Initialize normalizer (lazy import to avoid circular dependencies)
        self._normalizer = None

        # Ensure directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"ParsedCache initialized: {self.cache_dir}")

    @property
    def normalizer(self):
        """Lazy-load normalizer to avoid circular imports."""
        if self._normalizer is None:
            from omics_oracle_v2.lib.enrichment.fulltext.normalizer import ContentNormalizer

            self._normalizer = ContentNormalizer()
        return self._normalizer

    async def get(self, publication_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached parsed content for a publication.

        ENHANCED (Phase 4 - Oct 11, 2025):
        - Now also updates last_accessed timestamp in database
        - Enables usage tracking and analytics

        Args:
            publication_id: Unique identifier for the publication

        Returns:
            Cached content dict if found and not stale, None otherwise

        Example:
            >>> cached = await cache.get("PMC9876543")
            >>> if cached:
            >>>     print(f"Tables: {len(cached['content']['tables'])}")
        """
        # Try compressed file first (production)
        cache_file = self._get_cache_path(publication_id, compressed=True)

        if not cache_file.exists():
            # Try uncompressed (debugging)
            cache_file = self._get_cache_path(publication_id, compressed=False)

            if not cache_file.exists():
                logger.debug(f"Cache miss: {publication_id}")
                return None

        try:
            # Load cache file
            if cache_file.suffix == ".gz":
                with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(cache_file.read_text(encoding="utf-8"))

            # Check if stale
            if self._is_stale(data):
                logger.info(f"Cache stale: {publication_id} (age: {self._get_age_days(data)} days)")
                return None

            logger.info(f"OK Cache hit: {publication_id} (age: {self._get_age_days(data)} days)")

            # NEW (Phase 4): Update last accessed time in database
            try:
                from omics_oracle_v2.lib.enrichment.fulltext.cache_db import get_cache_db

                db = get_cache_db()
                db.update_access_time(publication_id)

            except Exception as db_error:
                # Don't fail if database update fails
                logger.debug(f"Failed to update access time in database: {db_error}")

            return data

        except Exception as e:
            logger.warning(f"Error reading cache for {publication_id}: {e}")
            # Delete corrupted cache file
            try:
                cache_file.unlink()
                logger.info(f"Deleted corrupted cache file: {cache_file}")
            except Exception:  # noqa: E722
                pass
            return None

    async def get_normalized(self, publication_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached content in normalized format.

        This method automatically converts content to the unified normalized
        format if needed. The normalized version is cached for future access.

        NEW (Phase 5 - Oct 11, 2025):
        - On-the-fly format normalization
        - All formats (JATS XML, PDF, LaTeX) -> Simple unified structure
        - Cached result for fast subsequent access
        - Enables format-agnostic downstream processing

        Args:
            publication_id: Unique identifier for the publication

        Returns:
            Normalized content dict if found, None otherwise

        Example:
            >>> # Get in normalized format (auto-converts if needed)
            >>> normalized = await cache.get_normalized("PMC9876543")
            >>>
            >>> # Now simple access regardless of original format!
            >>> methods = normalized['text']['sections'].get('methods', '')
            >>> tables = normalized['tables']
            >>> print(f"Found {len(tables)} tables")
        """
        # Get content (original or normalized)
        content = await self.get(publication_id)

        if content is None:
            return None

        # Check if already normalized
        metadata = content.get("metadata", {})
        if "normalized_version" in metadata:
            logger.debug(f"Content already normalized: {publication_id}")
            return content

        # Normalize on-the-fly
        logger.info(f"Normalizing {publication_id} from {content.get('source_type', 'unknown')} format")

        try:
            normalized = self.normalizer.normalize(content)

            # Save normalized version for next time
            # (This replaces the original, but we keep source_format in metadata)
            # Extract metadata carefully to avoid issues
            metadata = normalized.get("metadata", {})

            await self.save(
                publication_id=metadata.get("publication_id", publication_id),
                content=normalized,
                source_file=content.get("source_file"),
                source_type=metadata.get("source_format", content.get("source_type", "pdf")),
                parse_duration_ms=content.get("parse_duration_ms"),
                quality_score=content.get("quality_score"),
            )

            logger.info(f"OK Normalized and cached: {publication_id}")

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing {publication_id}: {e}")
            # Return original on error
            return content

    async def save(
        self,
        publication_id: str,
        content: Dict[str, Any],
        source_file: Optional[str] = None,
        source_type: str = "pdf",
        parse_duration_ms: Optional[int] = None,
        quality_score: Optional[float] = None,
        doi: Optional[str] = None,
        pmid: Optional[str] = None,
        pmc_id: Optional[str] = None,
    ) -> Path:
        """
        Save parsed content to cache.

        ENHANCED (Phase 4 - Oct 11, 2025):
        - Now also saves metadata to database for fast search
        - Tracks content characteristics (tables, figures, etc.)
        - Enables sub-millisecond queries

        Args:
            publication_id: Unique identifier for the publication
            content: Parsed content dict (tables, figures, sections, etc.)
            source_file: Path to source file that was parsed
            source_type: Type of source ('pdf', 'xml', 'nxml')
            parse_duration_ms: How long parsing took in milliseconds
            quality_score: Quality score of parsed content (0-1)
            doi: Digital Object Identifier (for database)
            pmid: PubMed ID (for database)
            pmc_id: PubMed Central ID (for database)

        Returns:
            Path where cache file was saved

        Example:
            >>> content = extract_structured_content(pdf_path)
            >>> cache_path = await cache.save(
            ...     publication_id="PMC9876543",
            ...     content=content,
            ...     source_file=str(pdf_path),
            ...     quality_score=0.95
            ... )
        """
        # Create cache entry
        cache_entry = {
            "publication_id": publication_id,
            "cached_at": datetime.now().isoformat(),
            "source_file": source_file,
            "source_type": source_type,
            "parse_duration_ms": parse_duration_ms,
            "quality_score": quality_score,
            "content": content,
        }

        # Determine cache file path
        cache_file = self._get_cache_path(publication_id, compressed=self.use_compression)

        try:
            # Save to cache
            if self.use_compression:
                with gzip.open(cache_file, "wt", encoding="utf-8") as f:
                    json.dump(cache_entry, f, indent=2)
            else:
                cache_file.write_text(json.dumps(cache_entry, indent=2), encoding="utf-8")

            file_size_kb = cache_file.stat().st_size // 1024
            logger.info(f"SAVED Cached parsed content: {publication_id} ({file_size_kb} KB)")

            # NEW (Phase 4): Save metadata to database for fast search
            try:
                from omics_oracle_v2.lib.enrichment.fulltext.cache_db import calculate_file_hash, get_cache_db

                db = get_cache_db()

                # Calculate file hash if source file exists
                file_hash = None
                file_size_bytes = None
                if source_file and Path(source_file).exists():
                    file_hash = calculate_file_hash(Path(source_file))
                    file_size_bytes = Path(source_file).stat().st_size

                # Determine file source from path
                file_source = "unknown"
                if source_file:
                    source_path = Path(source_file)
                    # Extract source from path like: data/fulltext/pdf/pmc/...
                    parts = source_path.parts
                    if "pdf" in parts or "xml" in parts:
                        idx = parts.index("pdf") if "pdf" in parts else parts.index("xml")
                        if idx + 1 < len(parts):
                            file_source = parts[idx + 1]

                # Extract content counts
                table_count = len(content.get("tables", []))
                figure_count = len(content.get("figures", []))
                section_count = len(content.get("sections", []))
                reference_count = len(content.get("references", []))

                # Calculate word count
                word_count = None
                if "text" in content:
                    word_count = len(content["text"].split())

                # Add to database
                db.add_entry(
                    publication_id=publication_id,
                    file_path=str(cache_file),
                    file_type=source_type,
                    file_source=file_source,
                    doi=doi,
                    pmid=pmid,
                    pmc_id=pmc_id,
                    file_hash=file_hash,
                    file_size_bytes=file_size_bytes,
                    table_count=table_count,
                    figure_count=figure_count,
                    section_count=section_count,
                    word_count=word_count,
                    reference_count=reference_count,
                    quality_score=quality_score,
                    parse_duration_ms=parse_duration_ms,
                )

                logger.debug(f"Added database metadata for {publication_id}")

            except Exception as db_error:
                # Don't fail the whole operation if database update fails
                logger.warning(f"Failed to update database metadata: {db_error}")

            return cache_file

        except Exception as e:
            logger.error(f"Error saving cache for {publication_id}: {e}")
            raise

    def delete(self, publication_id: str) -> bool:
        """
        Delete cached content for a publication.

        Args:
            publication_id: Publication to delete from cache

        Returns:
            True if deleted, False if not found
        """
        deleted = False

        # Try both compressed and uncompressed
        for compressed in [True, False]:
            cache_file = self._get_cache_path(publication_id, compressed=compressed)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Deleted cache: {publication_id}")
                deleted = True

        return deleted

    def clear_stale(self) -> int:
        """
        Delete all stale cache entries.

        Returns:
            Number of entries deleted
        """
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*.json*"):
            try:
                # Load and check if stale
                if cache_file.suffix == ".gz":
                    with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))

                if self._is_stale(data):
                    cache_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted stale cache: {cache_file.name}")

            except Exception as e:
                logger.warning(f"Error checking {cache_file.name}: {e}")
                # Delete corrupted files
                cache_file.unlink()
                deleted_count += 1

        logger.info(f"Cleared {deleted_count} stale cache entries")
        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        total_files = 0
        total_size_bytes = 0
        by_type = {}
        age_distribution = {"<7d": 0, "7-30d": 0, "30-90d": 0, ">90d": 0}

        for cache_file in self.cache_dir.glob("*.json*"):
            total_files += 1
            total_size_bytes += cache_file.stat().st_size

            try:
                # Load metadata
                if cache_file.suffix == ".gz":
                    with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))

                # Count by type
                source_type = data.get("source_type", "unknown")
                by_type[source_type] = by_type.get(source_type, 0) + 1

                # Age distribution
                age_days = self._get_age_days(data)
                if age_days < 7:
                    age_distribution["<7d"] += 1
                elif age_days < 30:
                    age_distribution["7-30d"] += 1
                elif age_days < 90:
                    age_distribution["30-90d"] += 1
                else:
                    age_distribution[">90d"] += 1

            except Exception:  # noqa: E722
                pass

        return {
            "total_entries": total_files,
            "total_size_mb": total_size_bytes / (1024 * 1024),
            "by_source_type": by_type,
            "age_distribution": age_distribution,
            "cache_dir": str(self.cache_dir),
            "ttl_days": self.ttl_days,
            "compression_enabled": self.use_compression,
        }

    def _get_cache_path(self, publication_id: str, compressed: bool = True) -> Path:
        """Get path for cache file."""
        filename = f"{publication_id}.json"
        if compressed:
            filename += ".gz"
        return self.cache_dir / filename

    def _is_stale(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is stale (older than TTL)."""
        try:
            cached_at = datetime.fromisoformat(cache_entry.get("cached_at", "2000-01-01"))
            age = datetime.now() - cached_at
            return age > timedelta(days=self.ttl_days)
        except Exception:  # noqa: E722
            return True  # If can't parse date, consider stale

    def _get_age_days(self, cache_entry: Dict[str, Any]) -> int:
        """Get age of cache entry in days."""
        try:
            cached_at = datetime.fromisoformat(cache_entry.get("cached_at", "2000-01-01"))
            age = datetime.now() - cached_at
            return age.days
        except Exception:  # noqa: E722
            return 999  # Unknown age


# Convenience function
def get_parsed_cache() -> ParsedCache:
    """
    Get a ParsedCache instance.

    This is a convenience function to avoid importing ParsedCache
    directly everywhere.

    Returns:
        ParsedCache instance
    """
    return ParsedCache()
