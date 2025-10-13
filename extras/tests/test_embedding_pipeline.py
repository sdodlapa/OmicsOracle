#!/usr/bin/env python3
"""
Test semantic search embedding with sample datasets.
This is a quick test to verify Phase 1 completion.
"""

import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_sample_datasets(cache_dir: str = "data/cache/geo_samples"):
    """Load sample GEO datasets from JSON files."""
    cache_path = Path(cache_dir)

    # Try combined file first
    combined_file = cache_path / "all_datasets.json"
    if combined_file.exists():
        logger.info(f"Loading from {combined_file}")
        with open(combined_file) as f:
            datasets = json.load(f)
        logger.info(f"✅ Loaded {len(datasets)} datasets from combined file")
        return datasets

    # Fall back to individual files
    datasets = []
    json_files = list(cache_path.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file) as f:
                dataset = json.load(f)
                datasets.append(dataset)
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")

    logger.info(f"✅ Loaded {len(datasets)} datasets from individual files")
    return datasets


def test_embedding_with_mock():
    """Test embedding pipeline with mock embeddings (no API key needed)."""
    print("=" * 80)
    print("Testing Semantic Search Embedding Pipeline")
    print("=" * 80)

    # Load datasets
    print("\n[1/5] Loading sample datasets...")
    datasets = load_sample_datasets()

    if not datasets:
        print("❌ No datasets found!")
        print("Run: python create_sample_datasets.py")
        return False

    print(f"✅ Loaded {len(datasets)} sample GEO datasets")

    # Create pipeline with mock embeddings
    print("\n[2/5] Initializing embedding pipeline (MOCK mode)...")

    from unittest.mock import MagicMock

    import numpy as np

    from omics_oracle_v2.lib.embeddings.geo_pipeline import GEOEmbeddingPipeline
    from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig

    embedding_config = EmbeddingConfig(api_key="mock")
    pipeline = GEOEmbeddingPipeline(embedding_config=embedding_config)

    # Replace with mock
    mock_service = MagicMock()
    mock_service.get_dimension.return_value = 128
    mock_service.embed_text.side_effect = lambda text: np.random.rand(128).tolist()
    pipeline.embedding_service = mock_service

    print("✅ Pipeline initialized with mock embeddings")

    # Embed datasets
    print(f"\n[3/5] Embedding {len(datasets)} datasets...")
    embedded_count = pipeline.embed_datasets(datasets, batch_size=5, show_progress=True)
    print(f"✅ Successfully embedded {embedded_count} datasets")

    # Show statistics
    print("\n[4/5] Pipeline Statistics:")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    # Save index
    print("\n[5/5] Saving vector index...")
    output_path = "data/vector_db/geo_index_test.faiss"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    saved_path = pipeline.save_index(output_path)
    file_size = Path(saved_path).stat().st_size / 1024  # KB
    print(f"✅ Index saved: {saved_path}")
    print(f"  Size: {file_size:.2f} KB")

    # Test search
    print("\n[TEST] Testing semantic search...")
    query_embedding = np.random.rand(128).tolist()
    results = pipeline.vector_db.search(query_embedding, k=3)

    print(f"✅ Search returned {len(results)} results:")
    for i, result in enumerate(results, 1):
        metadata = pipeline.vector_db.get_metadata(result["id"])
        print(f"  {i}. {result['id']}")
        print(f"     Title: {metadata.get('title', 'N/A')[:60]}...")
        print(f"     Score: {result['score']:.3f}")

    print("\n" + "=" * 80)
    print("✅ MOCK TEST PASSED - Pipeline is working!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Run with real embeddings:")
    print("   python -m omics_oracle_v2.scripts.embed_geo_datasets \\")
    print("       --cache-dir data/cache/geo_samples \\")
    print("       --output data/vector_db/geo_index.faiss")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_embedding_with_mock()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
