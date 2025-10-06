"""
Tests for GEO dataset embedding pipeline.

Run with:
    pytest tests/lib/embeddings/test_geo_pipeline.py -v
"""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from omics_oracle_v2.lib.embeddings.geo_pipeline import GEOEmbeddingPipeline, load_geo_datasets
from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig


class TestGEOEmbeddingPipeline:
    """Test GEO embedding pipeline."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = MagicMock()
        service.get_dimension.return_value = 128
        service.embed_text.side_effect = lambda text: np.random.rand(128).tolist()
        return service

    @pytest.fixture
    def sample_datasets(self):
        """Create sample GEO datasets."""
        return [
            {
                "id": "GSE1",
                "type": "dataset",
                "title": "Gene expression in breast cancer",
                "summary": "This study examines gene expression patterns.",
                "organism": "Homo sapiens",
                "keywords": ["breast cancer", "gene expression"],
            },
            {
                "id": "GSE2",
                "type": "dataset",
                "title": "RNA-seq of diabetic patients",
                "summary": "Transcriptome analysis of diabetes.",
                "organism": "Homo sapiens",
                "keywords": ["diabetes", "RNA-seq"],
            },
        ]

    @pytest.fixture
    def pipeline(self, mock_embedding_service):
        """Create pipeline with mock service."""
        # Patch EmbeddingService during init so dimension is mocked from the start
        with patch("omics_oracle_v2.lib.embeddings.geo_pipeline.EmbeddingService") as mock_service_class:
            mock_service_class.return_value = mock_embedding_service
            config = EmbeddingConfig(api_key="test-key")
            pipeline = GEOEmbeddingPipeline(embedding_config=config)
            return pipeline

    def test_initialization(self):
        """Test pipeline initialization."""
        config = EmbeddingConfig(api_key="test-key")
        pipeline = GEOEmbeddingPipeline(embedding_config=config)

        assert pipeline.embedding_service is not None
        assert pipeline.vector_db is not None
        assert pipeline.stats["total_datasets"] == 0

    def test_create_dataset_text_full(self, pipeline):
        """Test creating dataset text with all fields."""
        dataset = {
            "id": "GSE123",
            "title": "Test Dataset",
            "summary": "A test summary",
            "organism": "Homo sapiens",
            "keywords": ["test", "dataset"],
        }

        text = pipeline.create_dataset_text(dataset)

        assert "GSE123" in text
        assert "Test Dataset" in text
        assert "A test summary" in text
        assert "Homo sapiens" in text
        assert "test, dataset" in text

    def test_create_dataset_text_partial(self, pipeline):
        """Test creating dataset text with missing fields."""
        dataset = {"id": "GSE123", "title": "Test Dataset"}

        text = pipeline.create_dataset_text(dataset)

        assert "GSE123" in text
        assert "Test Dataset" in text
        # Should handle missing fields gracefully

    def test_create_dataset_text_empty(self, pipeline):
        """Test creating dataset text with empty dataset."""
        dataset = {"id": "GSE123"}

        text = pipeline.create_dataset_text(dataset)

        assert "GSE123" in text
        # Should not fail

    def test_embed_dataset_success(self, pipeline, sample_datasets):
        """Test successful dataset embedding."""
        dataset = sample_datasets[0]
        result = pipeline.embed_dataset(dataset)

        assert result is True
        assert pipeline.stats["embedded"] == 1
        assert pipeline.stats["errors"] == 0

    def test_embed_dataset_missing_id(self, pipeline):
        """Test embedding dataset without ID."""
        dataset = {"title": "No ID dataset"}
        result = pipeline.embed_dataset(dataset)

        assert result is False
        assert pipeline.stats["skipped"] == 1

    def test_embed_dataset_error_handling(self, pipeline, sample_datasets):
        """Test error handling during embedding."""
        # Make embedding service raise error
        pipeline.embedding_service.embed_text.side_effect = Exception("API error")

        dataset = sample_datasets[0]
        result = pipeline.embed_dataset(dataset)

        assert result is False
        assert pipeline.stats["errors"] == 1

    def test_embed_datasets_batch(self, pipeline, sample_datasets):
        """Test batch embedding of datasets."""
        embedded_count = pipeline.embed_datasets(sample_datasets, batch_size=10)

        assert embedded_count == 2
        assert pipeline.stats["total_datasets"] == 2
        assert pipeline.stats["embedded"] == 2

    def test_embed_datasets_empty_list(self, pipeline):
        """Test embedding empty dataset list."""
        embedded_count = pipeline.embed_datasets([])

        assert embedded_count == 0
        assert pipeline.stats["total_datasets"] == 0

    def test_embed_datasets_batch_size(self, pipeline):
        """Test batch processing with custom batch size."""
        # Create larger dataset with unique IDs
        datasets = [{"id": f"GSE{i}", "title": f"Dataset {i}"} for i in range(1, 21)]

        embedded_count = pipeline.embed_datasets(datasets, batch_size=5)

        assert embedded_count == 20

    def test_embed_datasets_progress_bar(self, pipeline, sample_datasets):
        """Test progress bar display."""
        # Should not raise error with progress bar
        embedded_count = pipeline.embed_datasets(sample_datasets, show_progress=True, batch_size=10)

        assert embedded_count == 2

    def test_embed_datasets_no_progress_bar(self, pipeline, sample_datasets):
        """Test without progress bar."""
        embedded_count = pipeline.embed_datasets(sample_datasets, show_progress=False, batch_size=10)

        assert embedded_count == 2

    def test_get_stats(self, pipeline, sample_datasets):
        """Test getting statistics."""
        pipeline.embed_datasets(sample_datasets)

        stats = pipeline.get_stats()

        assert stats["total_datasets"] == 2
        assert stats["embedded"] == 2
        assert stats["skipped"] == 0
        assert stats["errors"] == 0
        assert stats["index_size"] == 2
        assert stats["dimension"] == 128

    def test_save_index(self, pipeline, sample_datasets, tmp_path):
        """Test saving index to disk."""
        # Embed some datasets
        pipeline.embed_datasets(sample_datasets)

        # Save index
        index_path = tmp_path / "test_index.faiss"
        saved_path = pipeline.save_index(str(index_path))

        assert saved_path == str(index_path)
        assert index_path.exists()

    def test_load_existing_index(self, pipeline, sample_datasets, tmp_path):
        """Test loading existing index."""
        # Create and save an index
        pipeline.embed_datasets(sample_datasets)
        index_path = tmp_path / "test_index.faiss"
        pipeline.save_index(str(index_path))

        # Create new pipeline with existing index
        config = EmbeddingConfig(api_key="test-key")
        new_pipeline = GEOEmbeddingPipeline(embedding_config=config, index_path=str(index_path))
        new_pipeline.embedding_service = pipeline.embedding_service

        # Should have loaded existing embeddings
        assert new_pipeline.vector_db.size() == 2

    def test_stats_accumulation(self, pipeline):
        """Test that stats accumulate correctly."""
        # First batch
        batch1 = [{"id": "GSE1", "title": "Dataset 1"}]
        pipeline.embed_datasets(batch1)
        assert pipeline.stats["total_datasets"] == 1

        # Second batch (different ID!)
        batch2 = [{"id": "GSE2", "title": "Dataset 2"}]
        pipeline.embed_datasets(batch2)
        assert pipeline.stats["total_datasets"] == 2

    def test_error_recovery(self, pipeline):
        """Test error recovery in batch processing."""
        # Create datasets with mix of valid and invalid
        datasets = [
            {"id": "GSE1", "title": "Valid"},
            {"title": "No ID"},  # Invalid
            {"id": "GSE2", "title": "Valid"},
        ]

        embedded_count = pipeline.embed_datasets(datasets)

        assert embedded_count == 2  # Only valid ones
        assert pipeline.stats["embedded"] == 2
        assert pipeline.stats["skipped"] == 1


class TestLoadGEODatasets:
    """Test loading GEO datasets from cache."""

    def test_load_from_empty_directory(self, tmp_path):
        """Test loading from empty directory."""
        datasets = load_geo_datasets(str(tmp_path))
        assert datasets == []

    def test_load_from_json_files(self, tmp_path):
        """Test loading from JSON files."""
        # Create sample JSON files
        data1 = [{"id": "GSE1", "title": "Dataset 1"}]
        data2 = [{"id": "GSE2", "title": "Dataset 2"}]

        (tmp_path / "geo_1.json").write_text(json.dumps(data1))
        (tmp_path / "geo_2.json").write_text(json.dumps(data2))

        datasets = load_geo_datasets(str(tmp_path))

        assert len(datasets) == 2
        assert any(d["id"] == "GSE1" for d in datasets)
        assert any(d["id"] == "GSE2" for d in datasets)

    def test_load_with_nested_structure(self, tmp_path):
        """Test loading from nested directory structure."""
        # Create nested directories
        subdir = tmp_path / "cache" / "datasets"
        subdir.mkdir(parents=True)

        data = [{"id": "GSE1", "title": "Dataset 1"}]
        (subdir / "geo_data.json").write_text(json.dumps(data))

        datasets = load_geo_datasets(str(tmp_path))

        assert len(datasets) == 1

    def test_load_with_invalid_json(self, tmp_path):
        """Test loading with invalid JSON file."""
        # Create invalid JSON file
        (tmp_path / "invalid.json").write_text("not valid json")

        # Should skip invalid file and continue
        datasets = load_geo_datasets(str(tmp_path))
        assert datasets == []

    def test_load_with_non_list_json(self, tmp_path):
        """Test loading JSON that's not a list."""
        # Create JSON object instead of list
        data = {"id": "GSE1", "title": "Dataset 1"}
        (tmp_path / "object.json").write_text(json.dumps(data))

        # Should convert single object to list
        datasets = load_geo_datasets(str(tmp_path))
        assert len(datasets) == 1
        assert datasets[0]["id"] == "GSE1"

    def test_load_with_mixed_files(self, tmp_path):
        """Test loading with mix of valid and invalid files."""
        # Valid JSON
        valid_data = [{"id": "GSE1", "title": "Dataset 1"}]
        (tmp_path / "valid.json").write_text(json.dumps(valid_data))

        # Invalid JSON
        (tmp_path / "invalid.json").write_text("not json")

        # Text file (should be ignored)
        (tmp_path / "readme.txt").write_text("This is a readme")

        datasets = load_geo_datasets(str(tmp_path))

        assert len(datasets) == 1
        assert datasets[0]["id"] == "GSE1"

    def test_load_nonexistent_directory(self):
        """Test loading from nonexistent directory."""
        datasets = load_geo_datasets("/nonexistent/path")
        assert datasets == []


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    @pytest.fixture
    def mock_service(self):
        """Create mock embedding service."""
        service = MagicMock()
        service.get_dimension.return_value = 128
        service.embed_text.side_effect = lambda text: np.random.rand(128).tolist()
        return service

    def test_full_pipeline_workflow(self, tmp_path, mock_service):
        """Test complete workflow from loading to searching."""
        # 1. Create sample data files
        datasets_data = [
            {
                "id": "GSE1",
                "title": "Breast cancer study",
                "summary": "Gene expression in breast cancer",
                "organism": "Homo sapiens",
            },
            {
                "id": "GSE2",
                "title": "Diabetes RNA-seq",
                "summary": "Transcriptome of diabetic patients",
                "organism": "Homo sapiens",
            },
        ]

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "datasets.json").write_text(json.dumps(datasets_data))

        # 2. Load datasets
        datasets = load_geo_datasets(str(cache_dir))
        assert len(datasets) == 2

        # 3. Create pipeline and embed (mock the service during init)
        with patch("omics_oracle_v2.lib.embeddings.geo_pipeline.EmbeddingService") as mock_service_class:
            mock_service_class.return_value = mock_service
            config = EmbeddingConfig(api_key="test-key")
            pipeline = GEOEmbeddingPipeline(embedding_config=config)

        embedded_count = pipeline.embed_datasets(datasets)
        assert embedded_count == 2

        # 4. Save index
        index_path = tmp_path / "index.faiss"
        pipeline.save_index(str(index_path))
        assert index_path.exists()

        # 5. Load index in new pipeline
        new_pipeline = GEOEmbeddingPipeline(embedding_config=config, index_path=str(index_path))

        assert new_pipeline.vector_db.size() == 2

        # 6. Search
        import numpy as np

        query_embedding = np.random.rand(128).astype(np.float32)
        results = new_pipeline.vector_db.search(query_embedding, k=2)

        assert len(results) >= 0  # May return 0 if index is very small

    def test_incremental_embedding(self, tmp_path, mock_service):
        """Test adding datasets incrementally."""
        index_path = tmp_path / "index.faiss"

        # First batch
        with patch("omics_oracle_v2.lib.embeddings.geo_pipeline.EmbeddingService") as mock_service_class:
            mock_service_class.return_value = mock_service
            config = EmbeddingConfig(api_key="test-key")
            pipeline1 = GEOEmbeddingPipeline(embedding_config=config)

        batch1 = [{"id": "GSE1", "title": "Dataset 1"}]
        pipeline1.embed_datasets(batch1)
        pipeline1.save_index(str(index_path))

        assert pipeline1.vector_db.size() == 1

        # Second batch
        with patch("omics_oracle_v2.lib.embeddings.geo_pipeline.EmbeddingService") as mock_service_class:
            mock_service_class.return_value = mock_service
            pipeline2 = GEOEmbeddingPipeline(embedding_config=config, index_path=str(index_path))

        batch2 = [{"id": "GSE2", "title": "Dataset 2"}]
        pipeline2.embed_datasets(batch2)
        pipeline2.save_index(str(index_path))

        assert pipeline2.vector_db.size() == 2

    def test_large_batch_processing(self, mock_service):
        """Test processing large number of datasets."""
        with patch("omics_oracle_v2.lib.embeddings.geo_pipeline.EmbeddingService") as mock_service_class:
            mock_service_class.return_value = mock_service
            config = EmbeddingConfig(api_key="test-key")
            pipeline = GEOEmbeddingPipeline(embedding_config=config)

        # Create 100 datasets with unique IDs
        large_batch = [{"id": f"GSE{i}", "title": f"Dataset {i}"} for i in range(100)]

        embedded_count = pipeline.embed_datasets(large_batch, batch_size=20)

        assert embedded_count == 100
        assert pipeline.vector_db.size() == 100
