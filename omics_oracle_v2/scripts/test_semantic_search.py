#!/usr/bin/env python3
"""
Test semantic search on embedded GEO datasets.

Usage:
    python -m omics_oracle_v2.scripts.test_semantic_search \\
        --index data/vector_db/geo_index.faiss \\
        --query "breast cancer gene expression"

Examples:
    # Interactive mode
    python -m omics_oracle_v2.scripts.test_semantic_search

    # Single query
    python -m omics_oracle_v2.scripts.test_semantic_search \\
        --query "alzheimer's disease brain samples"

    # With custom top-k
    python -m omics_oracle_v2.scripts.test_semantic_search \\
        --query "diabetes RNA-seq" --top-k 5
"""

import argparse
import sys
from pathlib import Path

from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig, EmbeddingService
from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test semantic search on GEO datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--index",
        type=str,
        default="data/vector_db/geo_index.faiss",
        help="Path to FAISS index (default: data/vector_db/geo_index.faiss)",
    )

    parser.add_argument(
        "--query",
        type=str,
        help="Search query (if not provided, enters interactive mode)",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)",
    )

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
        help="Embedding model (default: text-embedding-3-small)",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    )

    return parser.parse_args()


def search(
    query: str,
    vector_db: FAISSVectorDB,
    embedding_service: EmbeddingService,
    top_k: int = 10,
) -> list:
    """Perform semantic search."""
    # Get query embedding
    query_embedding = embedding_service.embed_text(query)

    # Search
    results = vector_db.search(query_embedding, k=top_k)

    return results


def display_results(query: str, results: list):
    """Display search results."""
    print(f"\n{'=' * 80}")
    print(f"Query: {query}")
    print(f"{'=' * 80}\n")

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})

        print(f"[{i}] Score: {result['score']:.4f}")
        print(f"    ID: {metadata.get('id', 'N/A')}")
        print(f"    Type: {metadata.get('type', 'N/A')}")

        # Show dataset-specific metadata
        if metadata.get("type") == "dataset":
            print(f"    Title: {metadata.get('title', 'N/A')}")
            print(f"    Organism: {metadata.get('organism', 'N/A')}")

            # Show summary (truncated)
            summary = metadata.get("summary", "")
            if summary:
                summary_short = summary[:150] + "..." if len(summary) > 150 else summary
                print(f"    Summary: {summary_short}")

        print()


def interactive_mode(vector_db: FAISSVectorDB, embedding_service: EmbeddingService, top_k: int):
    """Interactive search mode."""
    print("=" * 80)
    print("Semantic Search - Interactive Mode")
    print("=" * 80)
    print(f"Index loaded: {vector_db.count()} embeddings")
    print(f"Dimension: {vector_db.dimension}")
    print(f"Top-k: {top_k}")
    print("\nEnter your queries (or 'quit' to exit)")
    print("=" * 80)

    while True:
        try:
            query = input("\nQuery: ").strip()

            if query.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if not query:
                continue

            results = search(query, vector_db, embedding_service, top_k)
            display_results(query, results)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")


def main():
    """Main entry point."""
    args = parse_args()

    # Check index exists
    index_path = Path(args.index)
    if not index_path.exists():
        print(f"[ERROR] Index not found: {args.index}")
        print("   Run embed_geo_datasets.py first to create the index")
        sys.exit(1)

    # Load index
    print(f"Loading index from {args.index}...")
    vector_db = FAISSVectorDB()
    vector_db.load(args.index)
    print(f"[OK] Loaded {vector_db.count()} embeddings (dimension: {vector_db.dimension})")

    # Create embedding service
    print("\nConfiguring embedding service...")
    print(f"   Provider: {args.provider}")
    print(f"   Model: {args.model}")

    if args.provider == "mock":
        print("   [WARNING] Using mock embeddings")
        from unittest.mock import MagicMock

        import numpy as np

        mock_service = MagicMock()
        mock_service.get_dimension.return_value = vector_db.dimension
        mock_service.embed_text.side_effect = lambda text: np.random.rand(vector_db.dimension).tolist()
        embedding_service = mock_service
    else:
        embedding_config = EmbeddingConfig(api_key=args.api_key, model=args.model)
        embedding_service = EmbeddingService(embedding_config)

    # Run search
    if args.query:
        # Single query mode
        results = search(args.query, vector_db, embedding_service, args.top_k)
        display_results(args.query, results)
    else:
        # Interactive mode
        interactive_mode(vector_db, embedding_service, args.top_k)

    return 0


if __name__ == "__main__":
    sys.exit(main())
