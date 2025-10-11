"""
Test QueryOptimizer with Production Tools

Tests integration of:
- BiomedicalNER (SciSpaCy)
- SynonymExpander (SapBERT + ontologies)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.query.optimizer import QueryOptimizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


async def test_query_optimizer():
    """Test QueryOptimizer with production tools."""

    print("=" * 80)
    print("QueryOptimizer Test - Production Tools Integration")
    print("=" * 80)

    # Initialize with all features enabled
    optimizer = QueryOptimizer(
        enable_ner=True,
        enable_synonyms=True,
        enable_expansion=True,
        enable_normalization=True,
        enable_sapbert=True,  # ✨ SapBERT enabled!
    )

    test_queries = [
        "alzheimer's disease",
        "APOE gene expression in Alzheimer's disease",
        "breast cancer treatment",
        "diabetes and insulin resistance",
        "TP53 mutations in cancer",
        "RNA-seq analysis of tumor samples",
        "ChIP-seq for histone modifications",
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"{'='*80}")

        try:
            result = await optimizer.optimize(query)

            print(f"\n📊 Optimization Result:")
            print(f"  Primary Query: {result.primary_query}")

            if result.entities:
                print(f"\n🔍 Entities Detected:")
                for entity_type, entities in result.entities.items():
                    print(f"  {entity_type.upper()}: {entities}")

            if result.synonyms:
                print(f"\n📖 Synonyms Found:")
                for term, syns in result.synonyms.items():
                    print(f"  '{term}':")
                    for syn in syns[:5]:  # Show first 5
                        print(f"    - {syn}")

            if result.expanded_terms:
                print(f"\n🔄 Expanded Terms:")
                for term in result.expanded_terms[:5]:  # Show first 5
                    print(f"  - {term}")

            if result.normalized_terms:
                print(f"\n✨ Normalized Terms:")
                for original, normalized in result.normalized_terms.items():
                    print(f"  '{original}' → '{normalized}'")

            # Get query variations
            variations = result.get_all_query_variations(max_per_type=2)
            print(f"\n📝 Query Variations (first 5):")
            for i, var in enumerate(variations[:5], 1):
                print(f"  {i}. {var}")

            print(f"\n✅ Total query variations: {len(variations)}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()


async def test_production_tools_status():
    """Check status of production tools."""

    print("\n" + "=" * 80)
    print("Production Tools Status Check")
    print("=" * 80)

    # Check BiomedicalNER
    try:
        from omics_oracle_v2.lib.nlp.biomedical_ner import BiomedicalNER

        ner = BiomedicalNER()
        model_info = ner.get_model_info()
        print(f"\n✅ BiomedicalNER: Available")
        print(f"   Model: {model_info.model_name}")
        print(f"   Version: {model_info.model_version}")
        print(f"   SciSpaCy: {model_info.has_scispacy}")
    except Exception as e:
        print(f"\n❌ BiomedicalNER: Not available ({e})")

    # Check SynonymExpander
    try:
        from omics_oracle_v2.lib.nlp.synonym_expansion import SynonymExpander, SynonymExpansionConfig

        config = SynonymExpansionConfig(
            use_embeddings=True,
            embedding_model="cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
        )
        expander = SynonymExpander(config)
        print(f"\n✅ SynonymExpander: Available")
        print(f"   SapBERT enabled: {config.use_embeddings}")
        print(f"   Model: {config.embedding_model}")
        print(f"   Ontologies: {', '.join(config.ontology_sources)}")
    except Exception as e:
        print(f"\n❌ SynonymExpander: Not available ({e})")

    print("\n" + "=" * 80)


async def main():
    """Run all tests."""

    # Check tool status first
    await test_production_tools_status()

    # Test query optimizer
    await test_query_optimizer()

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
