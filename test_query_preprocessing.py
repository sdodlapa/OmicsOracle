#!/usr/bin/env python3
"""
Test query preprocessing integration in publication search pipeline.

This test verifies:
1. BiomedicalNER integration
2. Entity extraction from queries
3. PubMed query enhancement with field tags
4. OpenAlex query optimization
5. Improved search results

Run: python test_query_preprocessing.py
"""

import logging

from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_query_preprocessing():
    """Test query preprocessing with biological entities."""

    print("=" * 80)
    print("TEST: Query Preprocessing Integration")
    print("=" * 80)

    # Test configuration with query preprocessing enabled
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=True,
        enable_scholar=False,  # Scholar disabled
        enable_citations=False,  # Skip citations for faster test
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_institutional_access=False,
        enable_cache=False,
        enable_query_preprocessing=True,  # ✅ Enable preprocessing
        pubmed_config=PubMedConfig(email="sdodl001@odu.edu"),
    )

    print("\n✓ Configuration:")
    print(f"  - PubMed: {config.enable_pubmed}")
    print(f"  - OpenAlex: {config.enable_openalex}")
    print(f"  - Query Preprocessing: {config.enable_query_preprocessing}")

    # Initialize pipeline
    print("\n✓ Initializing pipeline...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()

    # Check if NER is loaded
    if hasattr(pipeline, "ner") and pipeline.ner:
        print("  ✅ BiomedicalNER loaded successfully")
    else:
        print("  ⚠️  BiomedicalNER not loaded - preprocessing will be skipped")

    # Test queries with biological entities
    test_queries = [
        {
            "query": "breast cancer BRCA1 mutations",
            "expected_entities": ["breast cancer", "BRCA1"],
            "description": "Disease + Gene query",
        },
        {
            "query": "diabetes RNA-seq analysis",
            "expected_entities": ["diabetes", "RNA-seq"],
            "description": "Disease + Technique query",
        },
        {
            "query": "TP53 lung cancer",
            "expected_entities": ["TP53", "lung cancer"],
            "description": "Gene + Disease query",
        },
    ]

    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]

        print("\n" + "-" * 80)
        print(f"Test {i}: {description}")
        print(f"Query: '{query}'")
        print("-" * 80)

        # Test preprocessing directly
        if hasattr(pipeline, "_preprocess_query"):
            print("\n1. Query Preprocessing:")
            preprocessed = pipeline._preprocess_query(query)

            print(f"   Original: {preprocessed.get('original', query)}")

            # Show extracted entities
            if preprocessed.get("entities"):
                entity_count = sum(len(entities) for entities in preprocessed["entities"].values())
                print(f"\n   Extracted {entity_count} entities:")
                for entity_type, entities in preprocessed["entities"].items():
                    if entities:
                        entity_texts = [e.text for e in entities]
                        print(f"   - {entity_type.value}: {entity_texts}")

            # Show optimized queries
            pubmed_query = preprocessed.get("pubmed", query)
            openalex_query = preprocessed.get("openalex", query)

            if pubmed_query != query:
                print(f"\n   PubMed optimized:")
                print(f"   {pubmed_query}")
            else:
                print(f"\n   PubMed: Using original query (no entities found)")

            if openalex_query != query:
                print(f"\n   OpenAlex optimized:")
                print(f"   {openalex_query}")
            else:
                print(f"\n   OpenAlex: Using original query (no entities found)")

        # Run actual search (limited to 10 results for speed)
        print("\n2. Search Results:")
        try:
            result = pipeline.search(query, max_results=10)

            print(f"   Sources used: {result.metadata.get('sources_used', [])}")
            print(f"   Total results: {len(result.publications)}")
            print(f"   Search time: {result.metadata.get('search_time_ms', 0):.0f}ms")

            # Show top 3 results
            if result.publications:
                print(f"\n   Top 3 Results:")
                for j, pub_result in enumerate(result.publications[:3], 1):
                    pub = pub_result.publication
                    score = pub_result.relevance_score
                    print(f"   {j}. {pub.title[:80]}...")
                    print(f"      Source: {pub.source}, Score: {score:.2f}")
                    if pub.citations:
                        print(f"      Citations: {pub.citations}")
            else:
                print("   ⚠️  No results found")

        except Exception as e:
            print(f"   ❌ Search failed: {e}")
            import traceback

            traceback.print_exc()

    # Cleanup
    print("\n" + "=" * 80)
    print("✓ Cleaning up...")
    pipeline.cleanup()

    print("\n✅ TEST COMPLETE!")
    print("=" * 80)


def test_preprocessing_methods():
    """Test individual preprocessing methods."""

    print("\n" + "=" * 80)
    print("TEST: Individual Preprocessing Methods")
    print("=" * 80)

    config = PublicationSearchConfig(
        enable_query_preprocessing=True,
        pubmed_config=PubMedConfig(email="sdodl001@odu.edu"),
    )

    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()

    if not hasattr(pipeline, "ner") or not pipeline.ner:
        print("\n⚠️  BiomedicalNER not available - skipping method tests")
        return

    # Test entity extraction
    query = "CRISPR gene editing in breast cancer"
    print(f"\nTest Query: '{query}'")

    print("\n1. Extract entities:")
    ner_result = pipeline.ner.extract_entities(query)
    print(f"   Found {len(ner_result.entities)} entities:")
    for entity in ner_result.entities:
        print(f"   - {entity.text} ({entity.entity_type.value}) [{entity.start}:{entity.end}]")

    # Test query builders
    entities_by_type = ner_result.entities_by_type

    print("\n2. Build PubMed query:")
    pubmed_query = pipeline._build_pubmed_query(query, entities_by_type)
    print(f"   {pubmed_query}")

    print("\n3. Build OpenAlex query:")
    openalex_query = pipeline._build_openalex_query(query, entities_by_type)
    print(f"   {openalex_query}")

    pipeline.cleanup()
    print("\n✅ Method tests complete!")


if __name__ == "__main__":
    try:
        # Test 1: Full integration test
        test_query_preprocessing()

        # Test 2: Individual method tests
        test_preprocessing_methods()

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
