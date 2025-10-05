"""
Embedding service for generating text embeddings.

Supports OpenAI embeddings with file-based caching for performance.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EmbeddingConfig(BaseModel):
    """Configuration for embedding service."""

    # OpenAI settings
    api_key: Optional[str] = Field(None, description="OpenAI API key")
    model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model to use (text-embedding-3-small or text-embedding-3-large)",
    )
    dimension: int = Field(default=1536, description="Embedding dimension")

    # Performance
    batch_size: int = Field(default=100, description="Batch size for embedding generation")
    max_retries: int = Field(default=3, description="Maximum API retry attempts")

    # Caching
    cache_enabled: bool = Field(default=True, description="Enable embedding caching")
    cache_dir: str = Field(default="data/embeddings/cache", description="Directory for embedding cache")


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI.

    Features:
    - OpenAI text-embedding-3-small/large support
    - File-based caching for performance
    - Batch processing
    - Automatic retry logic

    Example:
        >>> service = EmbeddingService()
        >>> embedding = service.embed_text("ATAC-seq chromatin accessibility")
        >>> len(embedding)
        1536
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize embedding service.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or EmbeddingConfig()

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.config.api_key)

        # Setup cache directory
        if self.config.cache_enabled:
            self.cache_dir = Path(self.config.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Embedding cache enabled at {self.cache_dir}")
        else:
            self.cache_dir = None
            logger.info("Embedding cache disabled")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.embed_text("chromatin accessibility")
            >>> isinstance(embedding, list)
            True
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.config.dimension

        # Check cache first
        if self.config.cache_enabled:
            cached = self._get_from_cache(text)
            if cached is not None:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached

        # Generate embedding via API
        try:
            response = self.client.embeddings.create(
                input=text, model=self.config.model, dimensions=self.config.dimension
            )
            embedding = response.data[0].embedding

            # Cache the result
            if self.config.cache_enabled:
                self._save_to_cache(text, embedding)

            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector on error
            return [0.0] * self.config.dimension

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Example:
            >>> service = EmbeddingService()
            >>> embeddings = service.embed_batch(["text1", "text2"])
            >>> len(embeddings)
            2
        """
        if not texts:
            return []

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]

            # Check cache for each text
            batch_embeddings = []
            texts_to_embed = []
            cache_indices = []

            for idx, text in enumerate(batch):
                if not text or not text.strip():
                    batch_embeddings.append([0.0] * self.config.dimension)
                    continue

                if self.config.cache_enabled:
                    cached = self._get_from_cache(text)
                    if cached is not None:
                        batch_embeddings.append(cached)
                        continue

                # Need to embed this text
                texts_to_embed.append(text)
                cache_indices.append(len(batch_embeddings))
                batch_embeddings.append(None)  # Placeholder

            # Generate embeddings for uncached texts
            if texts_to_embed:
                try:
                    response = self.client.embeddings.create(
                        input=texts_to_embed,
                        model=self.config.model,
                        dimensions=self.config.dimension,
                    )

                    # Insert embeddings at correct positions
                    for idx, embedding_data in enumerate(response.data):
                        embedding = embedding_data.embedding
                        position = cache_indices[idx]
                        batch_embeddings[position] = embedding

                        # Cache the result
                        if self.config.cache_enabled:
                            self._save_to_cache(texts_to_embed[idx], embedding)

                    logger.info(f"Generated {len(texts_to_embed)} embeddings in batch")

                except Exception as e:
                    logger.error(f"Failed to generate batch embeddings: {e}")
                    # Fill with zero vectors
                    for idx in cache_indices:
                        if batch_embeddings[idx] is None:
                            batch_embeddings[idx] = [0.0] * self.config.dimension

            embeddings.extend(batch_embeddings)

        return embeddings

    def get_dimension(self) -> int:
        """
        Get the embedding dimension.

        Returns:
            Embedding vector dimension
        """
        return self.config.dimension

    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        if not self.config.cache_enabled or not self.cache_dir:
            logger.warning("Cache not enabled, nothing to clear")
            return

        import shutil

        shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Embedding cache cleared")

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Args:
            text: Input text

        Returns:
            Hash-based cache key
        """
        # Use model + text hash as key
        content = f"{self.config.model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """
        Retrieve embedding from cache.

        Args:
            text: Text to look up

        Returns:
            Cached embedding or None if not found
        """
        if not self.cache_dir:
            return None

        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    return data["embedding"]
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                return None

        return None

    def _save_to_cache(self, text: str, embedding: List[float]) -> None:
        """
        Save embedding to cache.

        Args:
            text: Input text
            embedding: Generated embedding
        """
        if not self.cache_dir:
            return

        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w") as f:
                json.dump({"text": text[:100], "embedding": embedding}, f)
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")
