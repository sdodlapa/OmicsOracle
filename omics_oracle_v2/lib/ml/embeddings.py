"""
Biomarker Embedding System

This module provides embedding generation and similarity search for biomarkers
and publications using sentence transformers and FAISS.

Features:
- Generate semantic embeddings for biomarkers and publications
- Redis-backed embedding cache
- Fast similarity search using FAISS
- Batch processing support
"""

import logging
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from omics_oracle_v2.lib.cache.redis_client import AsyncRedisCache
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class BiomarkerEmbedder:
    """
    Generate embeddings for biomarkers and publications using sentence transformers.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache: Optional[AsyncRedisCache] = None,
    ):
        """
        Initialize the embedder.

        Args:
            model_name: Sentence transformer model to use
            cache: Optional Redis cache for embeddings
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.cache = cache

        logger.info(
            f"Initialized BiomarkerEmbedder with {model_name} "
            f"({self.embedding_dim}-dimensional embeddings)"
        )

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim)

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (batched for efficiency).

        Args:
            texts: List of texts to embed

        Returns:
            Array of embeddings (n_texts x embedding_dim)
        """
        if not texts:
            return np.zeros((0, self.embedding_dim))

        # Filter out empty texts, keep track of indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            return np.zeros((len(texts), self.embedding_dim))

        # Generate embeddings for valid texts
        valid_embeddings = self.model.encode(valid_texts, convert_to_numpy=True, show_progress_bar=False)

        # Create result array with zeros for empty texts
        embeddings = np.zeros((len(texts), self.embedding_dim))
        for i, embedding in zip(valid_indices, valid_embeddings):
            embeddings[i] = embedding

        return embeddings

    def embed_biomarker(self, biomarker_name: str, publications: List[Publication]) -> np.ndarray:
        """
        Create biomarker embedding from associated publications.

        Combines:
        - Biomarker name
        - Publication titles
        - Publication abstracts

        Args:
            biomarker_name: Name of the biomarker
            publications: Publications mentioning the biomarker

        Returns:
            Biomarker embedding vector
        """
        # Collect text from publications
        texts = [biomarker_name]

        for pub in publications[:10]:  # Use top 10 publications
            if pub.title:
                texts.append(pub.title)
            if pub.abstract:
                texts.append(pub.abstract[:500])  # First 500 chars

        # Combine all text
        combined_text = " ".join(texts)

        return self.embed_text(combined_text)

    def embed_publication(self, publication: Publication) -> np.ndarray:
        """
        Generate embedding for a publication.

        Args:
            publication: Publication to embed

        Returns:
            Publication embedding vector
        """
        # Combine title and abstract
        parts = []
        if publication.title:
            parts.append(publication.title)
        if publication.abstract:
            parts.append(publication.abstract[:1000])  # First 1000 chars

        text = " ".join(parts)
        return self.embed_text(text)

    async def get_cached_embedding(
        self, entity_id: str, entity_type: str = "biomarker"
    ) -> Optional[np.ndarray]:
        """
        Retrieve embedding from cache.

        Args:
            entity_id: Entity identifier (biomarker name or publication ID)
            entity_type: Type of entity ("biomarker" or "publication")

        Returns:
            Cached embedding or None if not found
        """
        if not self.cache:
            return None

        cache_key = f"embedding:{entity_type}:{entity_id}"
        cached = await self.cache.get(cache_key)

        if cached:
            # Convert from list back to numpy array
            if isinstance(cached, list):
                return np.array(cached, dtype=np.float32)
            return cached

        return None

    async def set_cached_embedding(
        self, entity_id: str, embedding: np.ndarray, entity_type: str = "biomarker"
    ) -> None:
        """
        Store embedding in cache.

        Args:
            entity_id: Entity identifier
            embedding: Embedding vector
            entity_type: Type of entity
        """
        if not self.cache:
            return

        cache_key = f"embedding:{entity_type}:{entity_id}"
        # Convert numpy array to list for JSON serialization
        await self.cache.set(cache_key, embedding.tolist(), ttl=7 * 24 * 60 * 60)  # 7 days


class SimilaritySearch:
    """
    Fast similarity search using FAISS.
    """

    def __init__(self, embedding_dim: int):
        """
        Initialize similarity search.

        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.id_to_name = {}  # Map from index ID to biomarker name
        self.name_to_id = {}  # Map from biomarker name to index ID
        self.embeddings = None  # Store embeddings for later use

        logger.info(f"Initialized SimilaritySearch with {embedding_dim} dimensions")

    def build_index(self, biomarker_names: List[str], embeddings: np.ndarray) -> None:
        """
        Build FAISS index from biomarker embeddings.

        Args:
            biomarker_names: List of biomarker names
            embeddings: Array of embeddings (n_biomarkers x embedding_dim)
        """
        if len(biomarker_names) != len(embeddings):
            raise ValueError("Number of names must match number of embeddings")

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Create FAISS index (using inner product for cosine similarity on normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings.astype(np.float32))

        # Store mappings
        self.id_to_name = {i: name for i, name in enumerate(biomarker_names)}
        self.name_to_id = {name: i for i, name in enumerate(biomarker_names)}
        self.embeddings = embeddings

        logger.info(f"Built FAISS index with {len(biomarker_names)} biomarkers")

    def find_similar(
        self, query_embedding: np.ndarray, k: int = 10, exclude_self: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Find k most similar biomarkers to query.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            exclude_self: Exclude exact matches (for when querying with a biomarker in the index)

        Returns:
            List of (biomarker_name, similarity_score) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Normalize query for cosine similarity
        query = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query)

        # Search (k+1 to account for potential self-match)
        search_k = k + 1 if exclude_self else k
        distances, indices = self.index.search(query, search_k)

        # Convert to results
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx == -1:  # FAISS returns -1 for invalid results
                continue

            biomarker = self.id_to_name[idx]
            # Skip if this is a self-match and we want to exclude it
            if exclude_self and score > 0.999:  # Very close to 1.0 (exact match)
                continue

            results.append((biomarker, float(score)))

            if len(results) >= k:
                break

        return results

    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity (0 to 1)
        """
        # Normalize
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def get_embedding_by_name(self, biomarker_name: str) -> Optional[np.ndarray]:
        """
        Get embedding for a biomarker by name.

        Args:
            biomarker_name: Name of biomarker

        Returns:
            Embedding vector or None if not found
        """
        idx = self.name_to_id.get(biomarker_name)
        if idx is None or self.embeddings is None:
            return None

        return self.embeddings[idx]


class EmbeddingCache:
    """
    Redis-backed cache for embeddings with async support.
    """

    def __init__(self, redis_cache: AsyncRedisCache):
        """
        Initialize embedding cache.

        Args:
            redis_cache: Redis cache instance
        """
        self.cache = redis_cache

    async def get_embedding(self, entity_id: str, entity_type: str = "biomarker") -> Optional[np.ndarray]:
        """
        Retrieve embedding from cache.

        Args:
            entity_id: Entity identifier
            entity_type: Type of entity

        Returns:
            Embedding or None if not cached
        """
        key = f"embedding:{entity_type}:{entity_id}"
        cached = await self.cache.get(key)

        if cached:
            if isinstance(cached, list):
                return np.array(cached, dtype=np.float32)
            return cached

        return None

    async def set_embedding(
        self,
        entity_id: str,
        embedding: np.ndarray,
        entity_type: str = "biomarker",
        ttl: int = 7 * 24 * 60 * 60,
    ) -> None:
        """
        Store embedding in cache.

        Args:
            entity_id: Entity identifier
            embedding: Embedding vector
            entity_type: Type of entity
            ttl: Time to live in seconds (default: 7 days)
        """
        key = f"embedding:{entity_type}:{entity_id}"
        await self.cache.set(key, embedding.tolist(), ttl=ttl)

    async def get_batch(
        self, entity_ids: List[str], entity_type: str = "biomarker"
    ) -> Dict[str, Optional[np.ndarray]]:
        """
        Retrieve multiple embeddings from cache.

        Args:
            entity_ids: List of entity identifiers
            entity_type: Type of entities

        Returns:
            Dictionary mapping entity_id to embedding (or None if not cached)
        """
        results = {}
        for entity_id in entity_ids:
            results[entity_id] = await self.get_embedding(entity_id, entity_type)

        return results

    async def set_batch(
        self,
        embeddings: Dict[str, np.ndarray],
        entity_type: str = "biomarker",
        ttl: int = 7 * 24 * 60 * 60,
    ) -> None:
        """
        Store multiple embeddings in cache.

        Args:
            embeddings: Dictionary mapping entity_id to embedding
            entity_type: Type of entities
            ttl: Time to live in seconds
        """
        for entity_id, embedding in embeddings.items():
            await self.set_embedding(entity_id, embedding, entity_type, ttl)
