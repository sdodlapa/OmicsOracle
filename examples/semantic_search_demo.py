"""
Semantic Search Demo

Demonstrates the Phase 1-Lite semantic search capabilities:
- Document indexing with embeddings
- Hybrid keyword + semantic search
- Configurable ranking weights
"""

import numpy as np


# Mock embedding service for demo (no OpenAI API needed)
class MockEmbeddingService:
    """Simple mock embedding service for demonstration."""

    def __init__(self, dimension=128):
        self.dimension = dimension
        np.random.seed(42)

    def embed_text(self, text):
        hash_val = hash(text) % (2**32)
        np.random.seed(hash_val)
        embedding = np.random.randn(self.dimension)
        return (embedding / np.linalg.norm(embedding)).tolist()

    def embed_batch(self, texts):
        return [self.embed_text(text) for text in texts]

    def get_dimension(self):
        return self.dimension


def main():
    """Run semantic search demonstration."""
    print("=" * 70)
    print("PHASE 1-LITE: SEMANTIC SEARCH DEMONSTRATION")
    print("=" * 70)
    print()

    # Import components
    from omics_oracle_v2.lib.search.hybrid import HybridSearchEngine
    from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB

    # Step 1: Create components
    print("[*] Step 1: Initializing Components")
    print("-" * 70)

    embedding_service = MockEmbeddingService(dimension=128)
    vector_db = FAISSVectorDB(dimension=128)
    search_engine = HybridSearchEngine(embedding_service, vector_db)

    print("[+] Embedding Service: {}D vectors".format(embedding_service.dimension))
    print("[+] Vector Database: FAISS IndexFlatL2")
    print("[+] Search Engine: Hybrid (keyword + semantic)")
    print()

    # Step 2: Index sample biomedical datasets
    print("[*] Step 2: Indexing Sample Datasets")
    print("-" * 70)

    sample_datasets = [
        {
            "id": "GSE123001",
            "text": ("Single cell RNA sequencing of tumor microenvironment " "in breast cancer"),
            "title": "Breast Cancer Tumor Microenvironment",
            "organism": "Homo sapiens",
            "platform": "scRNA-Seq",
        },
        {
            "id": "GSE123002",
            "text": ("Gene expression profiling in pancreatic cancer using RNA-seq"),
            "title": "Pancreatic Cancer Gene Expression",
            "organism": "Homo sapiens",
            "platform": "RNA-Seq",
        },
        {
            "id": "GSE123003",
            "text": ("Proteomics analysis of Alzheimer's disease brain tissue"),
            "title": "Alzheimer's Disease Proteomics",
            "organism": "Homo sapiens",
            "platform": "Mass Spectrometry",
        },
        {
            "id": "GSE123004",
            "text": ("ChIP-seq analysis of histone modifications " "in embryonic stem cells"),
            "title": "Stem Cell Epigenetics",
            "organism": "Mus musculus",
            "platform": "ChIP-Seq",
        },
        {
            "id": "GSE123005",
            "text": ("Microarray gene expression in type 2 diabetes " "mellitus patients"),
            "title": "Diabetes Gene Expression",
            "organism": "Homo sapiens",
            "platform": "Microarray",
        },
        {
            "id": "GSE123006",
            "text": ("ATAC-seq chromatin accessibility in immune cells " "during inflammation"),
            "title": "Immune Cell Chromatin Dynamics",
            "organism": "Homo sapiens",
            "platform": "ATAC-Seq",
        },
        {
            "id": "GSE123007",
            "text": "Spatial transcriptomics of heart tissue in cardiac disease",
            "title": "Cardiac Disease Spatial Transcriptomics",
            "organism": "Homo sapiens",
            "platform": "Spatial Transcriptomics",
        },
        {
            "id": "GSE123008",
            "text": "Whole genome sequencing of hereditary cancer patients",
            "title": "Hereditary Cancer Genomics",
            "organism": "Homo sapiens",
            "platform": "WGS",
        },
    ]

    search_engine.index_documents(sample_datasets, metadata_fields=["title", "organism", "platform"])

    print("[+] Indexed {} datasets".format(search_engine.size()))
    print("   - Keyword index built")
    print("   - Vector embeddings generated")
    print("   - Metadata preserved")
    print()

    # Step 3: Perform searches with different configurations
    print("[*] Step 3: Search Demonstrations")
    print("=" * 70)
    print()

    # Demo 1: Balanced hybrid search
    print("Demo 1: Balanced Hybrid Search (40% keyword, 60% semantic)")
    print("-" * 70)
    query1 = "cancer gene expression RNA sequencing"
    print("Query: '{}'".format(query1))
    print()

    results1 = search_engine.search(query1)
    print("Found {} results:".format(len(results1)))
    for i, result in enumerate(results1[:5], 1):
        print("\n  {}. {} (rank {})".format(i, result.id, result.rank))
        print("     Title: {}".format(result.metadata.get("title", "N/A")))
        print("     Combined Score: {:.3f}".format(result.combined_score))
        print("     +- Keyword:  {:.3f}".format(result.keyword_score))
        print("     +- Semantic: {:.3f}".format(result.semantic_score))
    print()

    # Demo 2: Keyword-focused search
    print("\nDemo 2: Keyword-Focused Search (80% keyword, 20% semantic)")
    print("-" * 70)
    search_engine.update_config(keyword_weight=0.8, semantic_weight=0.2)

    query2 = "proteomics"
    print("Query: '{}'".format(query2))
    print()

    results2 = search_engine.search(query2)
    print("Found {} results:".format(len(results2)))
    for i, result in enumerate(results2[:3], 1):
        print("\n  {}. {}".format(i, result.id))
        print("     Title: {}".format(result.metadata.get("title", "N/A")))
        print("     Combined Score: {:.3f}".format(result.combined_score))
        print("     +- Keyword:  {:.3f} (*high weight*)".format(result.keyword_score))
        print("     +- Semantic: {:.3f}".format(result.semantic_score))
    print()

    # Demo 3: Semantic-focused search
    print("\nDemo 3: Semantic-Focused Search (20% keyword, 80% semantic)")
    print("-" * 70)
    search_engine.update_config(keyword_weight=0.2, semantic_weight=0.8)

    query3 = "transcriptome profiling"
    print("Query: '{}' (semantic similarity to RNA-seq)".format(query3))
    print()

    results3 = search_engine.search(query3)
    print("Found {} results:".format(len(results3)))
    for i, result in enumerate(results3[:3], 1):
        print("\n  {}. {}".format(i, result.id))
        print("     Title: {}".format(result.metadata.get("title", "N/A")))
        print("     Combined Score: {:.3f}".format(result.combined_score))
        print("     +- Keyword:  {:.3f}".format(result.keyword_score))
        print("     +- Semantic: {:.3f} (*high weight*)".format(result.semantic_score))
    print()

    # Demo 4: Filtered search
    print("\nDemo 4: Filtered Search (min combined score = 0.3)")
    print("-" * 70)
    search_engine.update_config(keyword_weight=0.5, semantic_weight=0.5, min_combined_score=0.3)

    query4 = "stem cells"
    print("Query: '{}'".format(query4))
    print()

    results4 = search_engine.search(query4)
    print("Found {} high-quality results (score >= 0.3):".format(len(results4)))
    for i, result in enumerate(results4, 1):
        print("\n  {}. {}".format(i, result.id))
        print("     Title: {}".format(result.metadata.get("title", "N/A")))
        print("     Combined Score: {:.3f} [OK]".format(result.combined_score))
    print()

    # Summary
    print("\n" + "=" * 70)
    print("[*] SUMMARY")
    print("=" * 70)
    print("[+] Total Datasets Indexed: {}".format(search_engine.size()))
    print("[+] Search Queries Executed: 4")
    print("[+] Configurations Tested: 4")
    print()
    print("Key Features Demonstrated:")
    print("  - Hybrid keyword + semantic search")
    print("  - Configurable ranking weights")
    print("  - Dynamic config updates")
    print("  - Score-based filtering")
    print("  - Metadata preservation")
    print("  - Result ranking and scoring")
    print()
    print("Phase 1-Lite MVP: [COMPLETE]")
    print("=" * 70)


if __name__ == "__main__":
    main()
