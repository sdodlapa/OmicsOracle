"""
GEO Dataset Embedding Pipeline.

Generates embeddings for GEO datasets and builds searchable vector index.
Supports batch processing, progress tracking, and resume capability.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig, EmbeddingService
from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB

logger = logging.getLogger(__name__)


class GEOEmbeddingPipeline:
    """
    Pipeline for embedding GEO datasets.

    Features:
    - Batch processing of datasets
    - Progress tracking and resume
    - Error handling and logging
    - Automatic index building
    - Metadata preservation

    Example:
        >>> pipeline = GEOEmbeddingPipeline()
        >>> pipeline.embed_datasets(datasets, batch_size=100)
        >>> pipeline.save_index("data/vector_db/geo_index.faiss")
    """

    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        index_path: Optional[Path] = None,
    ):
        """
        Initialize GEO embedding pipeline.

        Args:
            embedding_config: Configuration for embedding service
            index_path: Path to load/save vector index
        """
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.embedding_service = EmbeddingService(self.embedding_config)

        # Initialize vector database
        dimension = self.embedding_service.get_dimension()
        self.vector_db = FAISSVectorDB(dimension=dimension)

        self.index_path = index_path
        if self.index_path and Path(self.index_path).exists():
            logger.info(f"Loading existing index from {self.index_path}")
            self.vector_db.load(str(self.index_path))

        # Track statistics
        self.stats = {
            "total_datasets": 0,
            "embedded": 0,
            "skipped": 0,
            "errors": 0,
        }

    def create_dataset_text(self, dataset: Dict) -> str:
        """
        Create searchable text from dataset metadata.

        Combines title, summary, organism, and keywords into a single
        text representation for embedding.

        Args:
            dataset: Dataset metadata dictionary

        Returns:
            Combined text for embedding
        """
        parts = []

        # ID (for reference)
        dataset_id = dataset.get("id") or dataset.get("accession")
        if dataset_id:
            parts.append(f"ID: {dataset_id}")

        # Title (most important)
        if "title" in dataset and dataset["title"]:
            parts.append(f"Title: {dataset['title']}")

        # Summary/Description
        if "summary" in dataset and dataset["summary"]:
            parts.append(f"Summary: {dataset['summary']}")

        # Organism
        if "organism" in dataset and dataset["organism"]:
            organism = dataset["organism"]
            if isinstance(organism, list):
                organism = ", ".join(organism)
            parts.append(f"Organism: {organism}")

        # Keywords
        if "keywords" in dataset and dataset["keywords"]:
            keywords = dataset["keywords"]
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)
            parts.append(f"Keywords: {keywords}")

        # Sample type
        if "sample_type" in dataset and dataset["sample_type"]:
            parts.append(f"Sample Type: {dataset['sample_type']}")

        # Platform
        if "platform" in dataset and dataset["platform"]:
            platform = dataset["platform"]
            if isinstance(platform, list):
                platform = ", ".join(platform)
            parts.append(f"Platform: {platform}")

        return " ".join(parts)

    def embed_dataset(self, dataset: Dict) -> bool:
        """
        Embed a single dataset.

        Args:
            dataset: Dataset metadata dictionary

        Returns:
            True if successfully embedded, False otherwise
        """
        try:
            # Get dataset ID
            dataset_id = dataset.get("id") or dataset.get("accession")
            if not dataset_id:
                logger.warning("Dataset missing ID, skipping")
                self.stats["skipped"] += 1
                return False

            # Check if already embedded
            if self.vector_db.get_metadata(dataset_id):
                logger.debug(f"Dataset {dataset_id} already embedded, skipping")
                self.stats["skipped"] += 1
                return False

            # Create searchable text
            text = self.create_dataset_text(dataset)
            if not text or len(text.strip()) < 10:
                logger.warning(f"Dataset {dataset_id} has insufficient text, skipping")
                self.stats["skipped"] += 1
                return False

            # Generate embedding
            embedding = self.embedding_service.embed_text(text)

            # Prepare metadata (preserve original + add text)
            metadata = dict(dataset)
            metadata["text"] = text

            # Add to index immediately (convert to numpy array)
            import numpy as np

            embeddings_array = np.array([embedding], dtype=np.float32)
            self.vector_db.add_vectors(vectors=embeddings_array, ids=[dataset_id], metadata=[metadata])
            self.stats["embedded"] += 1
            return True

        except Exception as e:
            logger.error(f"Error embedding dataset {dataset.get('id', 'unknown')}: {e}")
            self.stats["errors"] += 1
            return False

    def embed_datasets(
        self,
        datasets: List[Dict],
        batch_size: int = 100,
        show_progress: bool = True,
    ) -> int:
        """
        Embed multiple datasets in batches.

        Args:
            datasets: List of dataset metadata dictionaries
            batch_size: Number of datasets to process at once (not used since we add immediately)
            show_progress: Whether to show progress bar

        Returns:
            Number of datasets successfully embedded
        """
        self.stats["total_datasets"] += len(datasets)
        logger.info(f"Starting embedding of {len(datasets)} datasets")

        # Process all datasets (batching happens at embed_dataset level)
        embedded_count = 0
        iterator = tqdm(datasets, desc="Embedding datasets") if show_progress else datasets

        for dataset in iterator:
            if self.embed_dataset(dataset):
                embedded_count += 1

        logger.info(
            f"Embedding complete: {embedded_count} embedded, "
            f"{self.stats['skipped']} skipped, {self.stats['errors']} errors"
        )

        return embedded_count

    def save_index(self, path: Optional[str] = None) -> str:
        """
        Save vector index to disk.

        Args:
            path: Path to save index (uses self.index_path if None)

        Returns:
            Path where index was saved
        """
        save_path = path or self.index_path or "data/vector_db/geo_index.faiss"
        save_path = str(save_path)

        logger.info(f"Saving index to {save_path}")
        self.vector_db.save(save_path)
        logger.info("Index saved successfully")

        return save_path

    def get_stats(self) -> Dict:
        """Get embedding statistics."""
        return {
            **self.stats,
            "index_size": self.vector_db.size(),
            "dimension": self.embedding_service.get_dimension(),
        }


def load_geo_datasets(cache_dir: str = "data/cache") -> List[Dict]:
    """
    Load GEO datasets from cache directory.

    Args:
        cache_dir: Directory containing cached GEO data

    Returns:
        List of dataset metadata dictionaries
    """
    cache_path = Path(cache_dir)
    datasets = []

    # Look for JSON files with GEO data
    json_files = list(cache_path.glob("**/*.json"))

    logger.info(f"Found {len(json_files)} JSON files in {cache_dir}")

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

                # Handle different data structures
                if isinstance(data, list):
                    datasets.extend(data)
                elif isinstance(data, dict):
                    # Could be single dataset or container
                    if "id" in data or "accession" in data:
                        datasets.append(data)
                    elif "datasets" in data:
                        datasets.extend(data["datasets"])
                    elif "results" in data:
                        datasets.extend(data["results"])
        except Exception as e:
            logger.warning(f"Error loading {json_file}: {e}")

    logger.info(f"Loaded {len(datasets)} datasets from cache")
    return datasets


# Demo usage
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 80)
    print("GEO Dataset Embedding Pipeline Demo")
    print("=" * 80)

    # Create sample datasets for demo
    sample_datasets = [
        {
            "id": "GSE123001",
            "title": "ATAC-seq analysis of chromatin accessibility in human T cells",
            "summary": "This study reveals dynamic changes in chromatin accessibility "
            "during T cell activation and identifies key regulatory elements.",
            "organism": "Homo sapiens",
            "keywords": ["ATAC-seq", "T cells", "chromatin accessibility"],
            "sample_type": "primary cells",
            "platform": "Illumina HiSeq 2500",
        },
        {
            "id": "GSE123002",
            "title": "RNA-seq profiling of gene expression in cancer cells",
            "summary": "Comprehensive transcriptome analysis reveals novel oncogenes "
            "and therapeutic targets in breast cancer.",
            "organism": "Homo sapiens",
            "keywords": ["RNA-seq", "cancer", "gene expression"],
            "sample_type": "cell line",
            "platform": "Illumina NovaSeq 6000",
        },
        {
            "id": "GSE123003",
            "title": "Single-cell ATAC-seq of developing mouse brain",
            "summary": "Identifies cell-type-specific regulatory landscapes in neural "
            "development using single-cell chromatin accessibility profiling.",
            "organism": "Mus musculus",
            "keywords": ["scATAC-seq", "brain development", "single-cell"],
            "sample_type": "tissue",
            "platform": "Illumina HiSeq 4000",
        },
    ]

    print("\n[*] Creating pipeline with mock embeddings for demo...")
    print("    (In production, set OPENAI_API_KEY environment variable)")

    # Use mock embeddings for demo
    embedding_config = EmbeddingConfig(api_key="dummy-for-demo")

    try:
        pipeline = GEOEmbeddingPipeline(
            embedding_config=embedding_config, index_path="data/vector_db/demo_index.faiss"
        )

        # Replace with mock embedding service for demo
        from unittest.mock import MagicMock

        import numpy as np

        mock_service = MagicMock()
        mock_service.get_dimension.return_value = 128
        mock_service.embed_text.side_effect = lambda text: np.random.rand(128).tolist()
        pipeline.embedding_service = mock_service

        print("\n[*] Embedding sample datasets...")
        embedded = pipeline.embed_datasets(sample_datasets, batch_size=10)

        print(f"\n[OK] Successfully embedded {embedded} datasets")

        # Show stats
        stats = pipeline.get_stats()
        print("\n[*] Pipeline Statistics:")
        for key, value in stats.items():
            print(f"    {key}: {value}")

        # Save index
        print("\n[*] Saving index...")
        index_path = pipeline.save_index()
        print(f"[OK] Index saved to: {index_path}")

        # Test search
        print("\n[*] Testing search...")
        query_embedding = np.random.rand(128).tolist()
        results = pipeline.vector_db.search(query_embedding, k=3)

        print(f"\n[OK] Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            metadata = pipeline.vector_db.get_metadata(result["id"])
            print(f"  {i}. {result['id']}: {metadata.get('title', 'N/A')}")
            print(f"     Score: {result['score']:.3f}")

        print("\n" + "=" * 80)
        print("Demo complete!")
        print("=" * 80)

    except Exception as e:
        print(f"\n[!] Error: {e}")
        print("[!] For full functionality, set OPENAI_API_KEY environment variable")
        sys.exit(1)
