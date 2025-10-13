#!/usr/bin/env python3
"""
Command-line tool for embedding GEO datasets.

Usage:
    python -m omics_oracle_v2.scripts.embed_geo_datasets \\
        --cache-dir data/cache \\
        --output data/vector_db/geo_index.faiss \\
        --batch-size 100 \\
        --model text-embedding-3-small

Examples:
    # Embed all datasets in cache
    python -m omics_oracle_v2.scripts.embed_geo_datasets

    # Embed with custom batch size
    python -m omics_oracle_v2.scripts.embed_geo_datasets --batch-size 50

    # Embed specific number of datasets
    python -m omics_oracle_v2.scripts.embed_geo_datasets --limit 1000

    # Use local model instead of OpenAI
    python -m omics_oracle_v2.scripts.embed_geo_datasets --provider local
"""

import argparse
import logging
import sys
from pathlib import Path

from omics_oracle_v2.lib.embeddings.geo_pipeline import GEOEmbeddingPipeline, load_geo_datasets
from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Embed GEO datasets for semantic search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input/Output
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/cache",
        help="Directory containing cached GEO datasets (default: data/cache)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/vector_db/geo_index.faiss",
        help="Output path for vector index (default: data/vector_db/geo_index.faiss)",
    )

    # Embedding configuration
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "local", "mock"],
        default="openai",
        help="Embedding provider (default: openai)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="text-embedding-3-small",
        help="Embedding model to use (default: text-embedding-3-small)",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )

    # Processing options
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of datasets to process at once (default: 100)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of datasets to embed (for testing)",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing index (skip already embedded datasets)",
    )

    # Display options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress bar",
    )

    return parser.parse_args()


def main():
    """Main entry point for CLI."""
    args = parse_args()

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    print("=" * 80)
    print("GEO Dataset Embedding Tool")
    print("=" * 80)

    # Load datasets
    print(f"\n[1/4] Loading datasets from {args.cache_dir}...")
    datasets = load_geo_datasets(args.cache_dir)

    if not datasets:
        print(f"[ERROR] No datasets found in {args.cache_dir}")
        print("   Make sure GEO datasets are cached in JSON format")
        sys.exit(1)

    print(f"[OK] Loaded {len(datasets)} datasets")

    # Apply limit if specified
    if args.limit:
        datasets = datasets[: args.limit]
        print(f"   Limited to {len(datasets)} datasets (--limit {args.limit})")

    # Create embedding configuration
    print("\n[2/4] Configuring embedding service...")
    print(f"   Provider: {args.provider}")
    print(f"   Model: {args.model}")

    if args.provider == "mock":
        print("   [WARNING] Using mock embeddings (for testing only)")
        embedding_config = EmbeddingConfig(api_key="mock-key")
    else:
        embedding_config = EmbeddingConfig(
            api_key=args.api_key,
            model=args.model,
        )

    # Create pipeline
    index_path = args.output if args.resume else None
    pipeline = GEOEmbeddingPipeline(embedding_config=embedding_config, index_path=index_path)

    # Use mock for demo if provider is mock
    if args.provider == "mock":
        from unittest.mock import MagicMock

        import numpy as np

        mock_service = MagicMock()
        mock_service.get_dimension.return_value = 128
        mock_service.embed_text.side_effect = lambda text: np.random.rand(128).tolist()
        pipeline.embedding_service = mock_service

    if args.resume:
        print("   Resume mode: loading existing index")
        existing_count = pipeline.vector_db.count()
        print(f"   Existing index has {existing_count} embeddings")

    # Embed datasets
    print(f"\n[3/4] Embedding {len(datasets)} datasets...")
    print(f"   Batch size: {args.batch_size}")
    print("   This may take a while...")
    print()

    try:
        embedded_count = pipeline.embed_datasets(
            datasets, batch_size=args.batch_size, show_progress=not args.quiet
        )

        print(f"\n[OK] Successfully embedded {embedded_count} datasets")

        # Show statistics
        stats = pipeline.get_stats()
        print("\n   Statistics:")
        print(f"   - Total datasets: {stats['total_datasets']}")
        print(f"   - Embedded: {stats['embedded']}")
        print(f"   - Skipped: {stats['skipped']}")
        print(f"   - Errors: {stats['errors']}")
        print(f"   - Index size: {stats['index_size']}")
        print(f"   - Dimension: {stats['dimension']}")

    except KeyboardInterrupt:
        print("\n\n[WARNING]  Interrupted by user")
        print("   Partial progress will be saved if --output specified")
    except Exception as e:
        print(f"\n[ERROR] Error during embedding: {e}")
        logger.exception("Embedding failed")
        sys.exit(1)

    # Save index
    print(f"\n[4/4] Saving index to {args.output}...")

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        saved_path = pipeline.save_index(args.output)
        print("[OK] Index saved successfully")
        print(f"   Path: {saved_path}")

        # Show file size
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        print(f"   Size: {file_size:.2f} MB")

    except Exception as e:
        print(f"[ERROR] Error saving index: {e}")
        logger.exception("Save failed")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("Embedding complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Test the index:")
    print("     python -m omics_oracle_v2.scripts.test_semantic_search")
    print("  2. Update SearchAgent to use the index")
    print("  3. Try semantic searches in the application")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
