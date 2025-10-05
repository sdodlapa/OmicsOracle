"""Verify all bug fixes are working."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.agents.models.search import RankedDataset
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata


def test_model_attributes():
    """Test that the models have the correct attributes."""

    print("\n" + "=" * 80)
    print("Testing Model Attributes")
    print("=" * 80 + "\n")

    # Test 1: GEOSeriesMetadata has pubmed_ids (plural)
    print("✓ Test 1: GEOSeriesMetadata attributes")
    test_metadata = GEOSeriesMetadata(
        geo_id="GSE123456", title="Test Dataset", pubmed_ids=["12345678", "87654321"]  # List
    )
    assert hasattr(test_metadata, "pubmed_ids"), "❌ Missing pubmed_ids"
    assert isinstance(test_metadata.pubmed_ids, list), "❌ pubmed_ids should be a list"
    assert not hasattr(test_metadata, "pubmed_id"), "❌ Should NOT have pubmed_id (singular)"
    print(f"  ✅ pubmed_ids exists and is a list: {test_metadata.pubmed_ids}")
    print(f"  ✅ has_publication check: bool(pubmed_ids) = {bool(test_metadata.pubmed_ids)}")

    # Test 2: has_sra_data method exists
    print("\n✓ Test 2: GEOSeriesMetadata.has_sra_data() method")
    assert hasattr(test_metadata, "has_sra_data"), "❌ Missing has_sra_data method"
    assert callable(test_metadata.has_sra_data), "❌ has_sra_data should be callable"
    result = test_metadata.has_sra_data()
    print(f"  ✅ has_sra_data() method exists and returns: {result}")

    # Test 3: RankedDataset structure
    print("\n✓ Test 3: RankedDataset nested structure")
    ranked = RankedDataset(dataset=test_metadata, relevance_score=0.85, match_reasons=["Title match"])
    assert hasattr(ranked, "dataset"), "❌ Missing dataset attribute"
    assert hasattr(ranked, "relevance_score"), "❌ Missing relevance_score"
    assert hasattr(ranked.dataset, "geo_id"), "❌ nested dataset should have geo_id"
    print(f"  ✅ RankedDataset.dataset exists")
    print(f"  ✅ RankedDataset.dataset.geo_id = {ranked.dataset.geo_id}")
    print(f"  ✅ RankedDataset.relevance_score = {ranked.relevance_score}")

    # Test 4: Proper access pattern
    print("\n✓ Test 4: Correct access pattern")
    ds = ranked.dataset  # Extract dataset first
    print(f"  ✅ ds = ranked.dataset")
    print(f"  ✅ ds.geo_id = {ds.geo_id}")
    print(f"  ✅ ds.pubmed_ids = {ds.pubmed_ids}")
    print(f"  ✅ bool(ds.pubmed_ids) = {bool(ds.pubmed_ids)}")
    print(f"  ✅ ranked.relevance_score = {ranked.relevance_score}")

    print("\n" + "=" * 80)
    print("✅ All model attribute tests passed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    test_model_attributes()
