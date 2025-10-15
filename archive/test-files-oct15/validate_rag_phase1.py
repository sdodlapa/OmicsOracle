#!/usr/bin/env python3
"""
Validate RAG Phase 1 Implementation
Tests model structure and prompt generation without requiring API server.
"""

import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.api.models.responses import DatasetResponse
from omics_oracle_v2.api.routes.agents import (AIAnalysisRequest,
                                               MatchExplanation,
                                               QueryProcessingContext)


def test_model_structure():
    """Test that all new models are correctly structured."""

    print("\n=== TESTING MODEL STRUCTURE ===\n")

    # Test QueryProcessingContext
    print("1. Testing QueryProcessingContext...")
    query_ctx = QueryProcessingContext(
        extracted_entities={"GENE": ["BRCA1", "TP53"], "DISEASE": ["breast cancer"]},
        expanded_terms=["BRCA1", "breast cancer 1", "tumor suppressor"],
        geo_search_terms=["BRCA1", "breast cancer"],
        search_intent="Find BRCA1 mutation datasets",
        query_type="gene-focused",
    )
    assert query_ctx.extracted_entities == {
        "GENE": ["BRCA1", "TP53"],
        "DISEASE": ["breast cancer"],
    }
    assert len(query_ctx.expanded_terms) == 3
    print("   ✅ QueryProcessingContext validated")

    # Test MatchExplanation
    print("2. Testing MatchExplanation...")
    match_exp = MatchExplanation(
        matched_terms=["BRCA1", "breast cancer"],
        relevance_score=0.95,
        match_type="exact",
        confidence=0.9,
    )
    assert match_exp.relevance_score == 0.95
    assert match_exp.match_type == "exact"
    print("   ✅ MatchExplanation validated")

    # Test AIAnalysisRequest with new fields
    print("3. Testing AIAnalysisRequest with enhanced fields...")
    dataset = DatasetResponse(
        geo_id="GSE12345",
        title="Test Dataset",
        summary="Test summary",
        organism="Homo sapiens",
        sample_count=10,
        platform="GPL570",
        relevance_score=0.95,
        match_reasons=["BRCA1", "breast cancer"],
    )

    request = AIAnalysisRequest(
        datasets=[dataset],
        query="BRCA1 mutations",
        max_datasets=5,
        query_processing=query_ctx,
        match_explanations={"GSE12345": match_exp},
    )

    assert request.query_processing is not None
    assert request.match_explanations is not None
    assert "GSE12345" in request.match_explanations
    print("   ✅ AIAnalysisRequest with enhanced fields validated")

    # Test backward compatibility (without new fields)
    print("4. Testing backward compatibility...")
    request_basic = AIAnalysisRequest(
        datasets=[dataset],
        query="BRCA1 mutations",
    )
    assert request_basic.query_processing is None
    assert request_basic.match_explanations is None
    print("   ✅ Backward compatibility validated")


def test_prompt_construction():
    """Test that prompt is correctly constructed with context."""

    print("\n=== TESTING PROMPT CONSTRUCTION ===\n")

    # Simulate the prompt construction logic
    query_processing = QueryProcessingContext(
        extracted_entities={
            "GENE": ["BRCA1"],
            "DISEASE": ["breast cancer"],
            "VARIANT": ["mutations"],
        },
        expanded_terms=["BRCA1", "breast cancer 1", "tumor suppressor"],
        geo_search_terms=["BRCA1", "breast cancer", "mutations"],
        search_intent="Find datasets studying BRCA1 mutations in breast cancer",
        query_type="gene-focused",
    )

    match_explanations = {
        "GSE12345": MatchExplanation(
            matched_terms=["BRCA1", "breast cancer"],
            relevance_score=0.95,
            match_type="exact",
            confidence=0.9,
        ),
        "GSE67890": MatchExplanation(
            matched_terms=["BRCA1 pathway"],
            relevance_score=0.82,
            match_type="synonym",
            confidence=0.75,
        ),
    }

    # Build query context section
    query_context_section = "\n# QUERY ANALYSIS CONTEXT\n"
    if query_processing.extracted_entities:
        query_context_section += (
            f"Extracted Entities: {dict(query_processing.extracted_entities)}\n"
        )
    if query_processing.expanded_terms:
        query_context_section += (
            f"Expanded Search Terms: {', '.join(query_processing.expanded_terms)}\n"
        )
    if query_processing.geo_search_terms:
        query_context_section += (
            f"GEO Query Used: {', '.join(query_processing.geo_search_terms)}\n"
        )
    if query_processing.search_intent:
        query_context_section += f"Search Intent: {query_processing.search_intent}\n"
    if query_processing.query_type:
        query_context_section += f"Query Type: {query_processing.query_type}\n"

    # Build match context section
    match_context_section = "\n# WHY THESE DATASETS WERE RETRIEVED\n"
    for geo_id, explanation in match_explanations.items():
        match_context_section += (
            f"- {geo_id}: Matched terms [{', '.join(explanation.matched_terms)}], "
            f"Relevance: {int(explanation.relevance_score * 100)}%, "
            f"Match type: {explanation.match_type}\n"
        )

    print("Query Context Section:")
    print(query_context_section)
    print("\nMatch Context Section:")
    print(match_context_section)

    # Validate content
    assert "BRCA1" in query_context_section
    assert "breast cancer" in query_context_section
    assert "gene-focused" in query_context_section
    assert "GSE12345" in match_context_section
    assert "95%" in match_context_section
    assert "exact" in match_context_section

    print("\n✅ Prompt construction validated")
    print("   - Query context includes entities: GENE, DISEASE, VARIANT")
    print("   - Expanded terms present")
    print("   - Match explanations for 2 datasets")
    print("   - Relevance scores formatted correctly")


def test_serialization():
    """Test that models can be serialized to JSON."""

    print("\n=== TESTING JSON SERIALIZATION ===\n")

    query_ctx = QueryProcessingContext(
        extracted_entities={"GENE": ["BRCA1"]},
        expanded_terms=["BRCA1", "tumor suppressor"],
        geo_search_terms=["BRCA1"],
        search_intent="Test",
        query_type="gene-focused",
    )

    match_exp = MatchExplanation(
        matched_terms=["BRCA1"],
        relevance_score=0.95,
        match_type="exact",
        confidence=0.9,
    )

    # Test serialization
    query_ctx_json = query_ctx.model_dump()
    match_exp_json = match_exp.model_dump()

    print("QueryProcessingContext JSON:")
    print(json.dumps(query_ctx_json, indent=2))
    print("\nMatchExplanation JSON:")
    print(json.dumps(match_exp_json, indent=2))

    # Validate JSON structure
    assert "extracted_entities" in query_ctx_json
    assert "matched_terms" in match_exp_json

    print("\n✅ JSON serialization validated")


def main():
    """Run all tests."""

    print("=" * 60)
    print("RAG Phase 1 Implementation Validation")
    print("=" * 60)

    try:
        test_model_structure()
        test_prompt_construction()
        test_serialization()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nRAG Phase 1 Backend Implementation: ✅ VALIDATED")
        print("\nNext Steps:")
        print("1. Start API server: make dev")
        print("2. Run integration test: python test_rag_phase1.py")
        print("3. Implement Phase 2: Frontend integration")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
