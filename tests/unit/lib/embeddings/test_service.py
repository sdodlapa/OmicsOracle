"""
Unit tests for embedding service.

Tests embedding generation, caching, and batch processing.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig, EmbeddingService


class TestEmbeddingConfig:
    """Test embedding configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EmbeddingConfig()

        assert config.model == "text-embedding-3-small"
        assert config.dimension == 1536
        assert config.batch_size == 100
        assert config.cache_enabled is True
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = EmbeddingConfig(
            model="text-embedding-3-large",
            dimension=3072,
            batch_size=50,
            cache_enabled=False,
        )

        assert config.model == "text-embedding-3-large"
        assert config.dimension == 3072
        assert config.batch_size == 50
        assert config.cache_enabled is False

    def test_config_values(self):
        """Test configuration values are correct."""
        config = EmbeddingConfig()

        assert config.model == "text-embedding-3-small"
        assert config.dimension == 1536
        assert config.batch_size == 100


class TestEmbeddingService:
    """Test embedding service."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_cache_dir):
        """Create test configuration."""
        return EmbeddingConfig(
            api_key="test-key",
            cache_enabled=True,
            cache_dir=temp_cache_dir,
        )

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        return mock_response

    def test_initialization(self, config):
        """Test service initialization."""
        service = EmbeddingService(config)

        assert service.config == config
        assert service.client is not None
        assert service.cache_dir == Path(config.cache_dir)

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_initialization_without_config(self, mock_openai_class):
        """Test initialization with default config."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Create config with API key
        config = EmbeddingConfig(api_key="test-key")
        service = EmbeddingService(config)

        assert service.config is not None
        assert service.config.model == "text-embedding-3-small"

    def test_get_dimension(self, config):
        """Test getting embedding dimension."""
        service = EmbeddingService(config)

        assert service.get_dimension() == 1536

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_text_success(self, mock_openai_class, config, mock_openai_response):
        """Test successful text embedding."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)
        embedding = service.embed_text("test text")

        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_client.embeddings.create.assert_called_once()

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_empty_text(self, mock_openai_class, config):
        """Test embedding empty text returns zero vector."""
        service = EmbeddingService(config)

        embedding = service.embed_text("")
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)

        embedding = service.embed_text("   ")
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_text_with_cache(self, mock_openai_class, config, mock_openai_response):
        """Test embedding caching."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)

        # First call - should hit API
        embedding1 = service.embed_text("test text")
        assert mock_client.embeddings.create.call_count == 1

        # Second call - should use cache
        embedding2 = service.embed_text("test text")
        assert mock_client.embeddings.create.call_count == 1  # No additional call
        assert embedding1 == embedding2

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_text_cache_disabled(self, mock_openai_class, config, mock_openai_response):
        """Test embedding without cache."""
        config.cache_enabled = False

        # Setup mock
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)

        # Both calls should hit API
        service.embed_text("test text")
        service.embed_text("test text")
        assert mock_client.embeddings.create.call_count == 2

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_text_api_error(self, mock_openai_class, config):
        """Test handling API errors."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)
        embedding = service.embed_text("test text")

        # Should return zero vector on error
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_batch_success(self, mock_openai_class, config):
        """Test successful batch embedding."""
        # Setup mock for batch
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
            MagicMock(embedding=[0.3] * 1536),
        ]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)
        texts = ["text1", "text2", "text3"]
        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        mock_client.embeddings.create.assert_called_once()

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_batch_empty(self, mock_openai_class, config):
        """Test batch embedding with empty list."""
        service = EmbeddingService(config)
        embeddings = service.embed_batch([])

        assert embeddings == []

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_batch_with_empty_texts(self, mock_openai_class, config):
        """Test batch embedding with some empty texts."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)
        texts = ["", "valid text", "   "]
        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 3
        # Empty texts should have zero vectors
        assert all(x == 0.0 for x in embeddings[0])
        assert all(x == 0.0 for x in embeddings[2])
        # Valid text should have real embedding
        assert embeddings[1] == [0.1] * 1536

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_batch_with_cache(self, mock_openai_class, config):
        """Test batch embedding uses cache."""
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
        ]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)

        # First batch
        texts1 = ["text1", "text2"]
        _ = service.embed_batch(texts1)
        assert mock_client.embeddings.create.call_count == 1

        # Second batch with one cached text
        texts2 = ["text1", "text3"]
        _ = service.embed_batch(texts2)
        # Should only embed text3 (text1 is cached)
        assert mock_client.embeddings.create.call_count == 2

    @patch("omics_oracle_v2.lib.embeddings.service.OpenAI")
    def test_embed_batch_large_batch(self, mock_openai_class, config):
        """Test batch embedding with batching."""
        config.batch_size = 2  # Small batch size for testing

        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
        ]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        service = EmbeddingService(config)

        # 5 texts should require 3 API calls (2+2+1)
        texts = [f"text{i}" for i in range(5)]
        embeddings = service.embed_batch(texts)

        assert len(embeddings) == 5
        assert mock_client.embeddings.create.call_count == 3

    def test_clear_cache(self, config):
        """Test clearing cache."""
        service = EmbeddingService(config)

        # Create a cache file
        cache_dir = Path(config.cache_dir)
        test_file = cache_dir / "test.json"
        test_file.write_text('{"test": "data"}')

        assert test_file.exists()

        # Clear cache
        service.clear_cache()

        # File should be gone
        assert not test_file.exists()
        # Directory should still exist
        assert cache_dir.exists()

    def test_clear_cache_disabled(self, config):
        """Test clearing cache when disabled."""
        config.cache_enabled = False
        service = EmbeddingService(config)

        # Should not raise error
        service.clear_cache()

    def test_cache_key_generation(self, config):
        """Test cache key generation."""
        service = EmbeddingService(config)

        key1 = service._get_cache_key("test text")
        key2 = service._get_cache_key("test text")
        key3 = service._get_cache_key("different text")

        # Same text should generate same key
        assert key1 == key2
        # Different text should generate different key
        assert key1 != key3

    def test_cache_persistence(self, config):
        """Test that cache persists across service instances."""
        # First service instance
        with patch("omics_oracle_v2.lib.embeddings.service.OpenAI") as mock_openai_class:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.5] * 1536)]

            mock_client = MagicMock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            service1 = EmbeddingService(config)
            embedding1 = service1.embed_text("persistent text")

        # Second service instance (new OpenAI client)
        with patch("omics_oracle_v2.lib.embeddings.service.OpenAI") as mock_openai_class2:
            mock_client2 = MagicMock()
            mock_openai_class2.return_value = mock_client2

            service2 = EmbeddingService(config)
            embedding2 = service2.embed_text("persistent text")

            # Should use cached embedding, not call API
            mock_client2.embeddings.create.assert_not_called()
            assert embedding1 == embedding2
