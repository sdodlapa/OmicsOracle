#!/usr/bin/env python3
"""
Test RAG Phase 1 Implementation
Tests the enhanced AI Analysis endpoint with query processing context.
"""

import asyncio
import logging

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8002"


async def test_enhanced_rag():
    """Test AI Analysis with enhanced RAG context."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Search for datasets
        logger.info("\n=== STEP 1: Search for datasets ===")
        search_response = await client.post(
            f"{BASE_URL}/api/search",
            json={"query": "BRCA1 mutations in breast cancer", "max_results": 5},
        )

        if search_response.status_code != 200:
            logger.error(f"Search failed: {search_response.status_code}")
            logger.error(search_response.text)
            return

        search_data = search_response.json()
        datasets = search_data.get("datasets", [])

        if not datasets:
            logger.warning("No datasets found")
            return

        logger.info(f"Found {len(datasets)} datasets")

        # Step 2: Prepare query processing context (simulated)
        logger.info("\n=== STEP 2: Prepare query context (simulated) ===")
        query_processing = {
            "extracted_entities": {
                "GENE": ["BRCA1"],
                "DISEASE": ["breast cancer"],
                "VARIANT": ["mutations"],
            },
            "expanded_terms": ["BRCA1", "breast cancer 1", "tumor suppressor", "DNA repair"],
            "geo_search_terms": ["BRCA1", "breast cancer", "mutations"],
            "search_intent": "Find datasets studying BRCA1 mutations in breast cancer",
            "query_type": "gene-focused",
        }

        logger.info(f"Query context: {query_processing}")

        # Step 3: Prepare match explanations (simulated)
        logger.info("\n=== STEP 3: Prepare match explanations (simulated) ===")
        match_explanations = {}
        for dataset in datasets[:3]:
            geo_id = dataset["geo_id"]
            match_reasons = dataset.get("match_reasons", [])

            match_explanations[geo_id] = {
                "matched_terms": ["BRCA1", "breast cancer"] if match_reasons else [],
                "relevance_score": dataset.get("relevance_score", 0.5),
                "match_type": "exact" if "BRCA1" in str(match_reasons) else "semantic",
                "confidence": dataset.get("relevance_score", 0.5),
            }

        logger.info(f"Match explanations for {len(match_explanations)} datasets")

        # Step 4: Test WITHOUT query context (backward compatibility)
        logger.info("\n=== STEP 4: Test WITHOUT query context (baseline) ===")
        baseline_request = {
            "query": "BRCA1 mutations in breast cancer",
            "datasets": datasets[:2],
            "max_datasets": 2,
        }

        logger.info("Calling AI Analysis (baseline)...")
        baseline_response = await client.post(
            f"{BASE_URL}/api/agents/analyze",
            json=baseline_request,
        )

        if baseline_response.status_code == 200:
            baseline_data = baseline_response.json()
            logger.info("\n--- BASELINE ANALYSIS (no context) ---")
            logger.info(f"Model: {baseline_data.get('model_used')}")
            logger.info(f"Execution time: {baseline_data.get('execution_time_ms'):.0f}ms")
            logger.info("\nAnalysis:")
            logger.info(baseline_data.get("analysis", "")[:500])
        else:
            logger.error(f"Baseline analysis failed: {baseline_response.status_code}")
            logger.error(baseline_response.text)

        # Step 5: Test WITH query context (enhanced RAG)
        logger.info("\n=== STEP 5: Test WITH query context (enhanced RAG) ===")
        enhanced_request = {
            "query": "BRCA1 mutations in breast cancer",
            "datasets": datasets[:2],
            "max_datasets": 2,
            "query_processing": query_processing,
            "match_explanations": match_explanations,
        }

        logger.info("Calling AI Analysis (enhanced)...")
        enhanced_response = await client.post(
            f"{BASE_URL}/api/agents/analyze",
            json=enhanced_request,
        )

        if enhanced_response.status_code == 200:
            enhanced_data = enhanced_response.json()
            logger.info("\n--- ENHANCED ANALYSIS (with context) ---")
            logger.info(f"Model: {enhanced_data.get('model_used')}")
            logger.info(f"Execution time: {enhanced_data.get('execution_time_ms'):.0f}ms")
            logger.info("\nAnalysis:")
            logger.info(enhanced_data.get("analysis", ""))

            # Step 6: Compare results
            logger.info("\n=== STEP 6: Quality comparison ===")
            baseline_text = baseline_data.get("analysis", "") if baseline_response.status_code == 200 else ""
            enhanced_text = enhanced_data.get("analysis", "")

            # Check for entity mentions
            entity_mentions_baseline = sum(
                1 for entity in ["BRCA1", "breast cancer", "mutations"] if entity in baseline_text
            )
            entity_mentions_enhanced = sum(
                1 for entity in ["BRCA1", "breast cancer", "mutations"] if entity in enhanced_text
            )

            logger.info(f"\nEntity mentions:")
            logger.info(f"  Baseline: {entity_mentions_baseline}/3")
            logger.info(f"  Enhanced: {entity_mentions_enhanced}/3")

            # Check for match explanation references
            match_refs_baseline = "matched" in baseline_text.lower() or "relevance" in baseline_text.lower()
            match_refs_enhanced = "matched" in enhanced_text.lower() or "relevance" in enhanced_text.lower()

            logger.info(f"\nMatch explanation references:")
            logger.info(f"  Baseline: {'Yes' if match_refs_baseline else 'No'}")
            logger.info(f"  Enhanced: {'Yes' if match_refs_enhanced else 'No'}")

            # Check for structured reasoning
            step_refs_baseline = "step" in baseline_text.lower()
            step_refs_enhanced = "step" in enhanced_text.lower()

            logger.info(f"\nStructured reasoning:")
            logger.info(f"  Baseline: {'Yes' if step_refs_baseline else 'No'}")
            logger.info(f"  Enhanced: {'Yes' if step_refs_enhanced else 'No'}")

            # Overall assessment
            logger.info("\n=== OVERALL ASSESSMENT ===")
            improvements = 0
            if entity_mentions_enhanced > entity_mentions_baseline:
                logger.info("✅ More entity mentions in enhanced version")
                improvements += 1
            if match_refs_enhanced and not match_refs_baseline:
                logger.info("✅ Match explanation references added")
                improvements += 1
            if step_refs_enhanced and not step_refs_baseline:
                logger.info("✅ Structured reasoning added")
                improvements += 1

            if improvements >= 2:
                logger.info("\n🎉 SUCCESS: Enhanced RAG shows significant improvements!")
            elif improvements == 1:
                logger.info("\n⚠️  PARTIAL: Enhanced RAG shows some improvements")
            else:
                logger.info("\n❌ CONCERN: Enhanced RAG not showing expected improvements")

        else:
            logger.error(f"Enhanced analysis failed: {enhanced_response.status_code}")
            logger.error(enhanced_response.text)


if __name__ == "__main__":
    asyncio.run(test_enhanced_rag())
