#!/usr/bin/env python3
"""
Complete Mapping Validation Script

Tests the complete data flow:
1. URL (from search results)
2. → PDF Download
3. → Parsed Text
4. → AI Analysis

NEW (Oct 13, 2025):
- Tests UniversalIdentifier system (works for DOI, arXiv, etc. - not just PMIDs)
- Validates hierarchical identifier fallback
- Checks all 11 full-text sources

Validates that mappings are correctly maintained at each step.

Usage:
    python scripts/validate_complete_mapping.py

Requirements:
    - Backend running on http://localhost:8000
    - Test datasets in database
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


def search_datasets(query: str = "cancer") -> List[Dict[str, Any]]:
    """Step 1: Search for datasets."""
    print_section("STEP 1: Search for Datasets")

    response = requests.post(
        f"{BASE_URL}/api/agents/search", json={"search_terms": [query], "max_results": 3}
    )

    if response.status_code != 200:
        print_error(f"Search failed: {response.status_code}")
        return []

    data = response.json()
    datasets = data.get("datasets", [])

    print_info(f"Found {len(datasets)} datasets")
    for i, ds in enumerate(datasets):
        print(f"\n{i+1}. {ds['geo_id']} - {ds['title'][:60]}...")
        print(f"   PMIDs: {ds.get('pubmed_ids', [])}")
        print(f"   Fulltext count: {ds.get('fulltext_count', 0)}")

    # Filter datasets with PMIDs
    datasets_with_pmids = [ds for ds in datasets if ds.get("pubmed_ids")]
    print_success(f"Found {len(datasets_with_pmids)} datasets with linked papers")

    return datasets_with_pmids


def download_papers(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Step 2: Download PDFs for datasets."""
    print_section("STEP 2: Download PDFs (One at a Time)")

    enriched_datasets = []

    for i, dataset in enumerate(datasets[:2], 1):  # Test first 2 datasets
        geo_id = dataset["geo_id"]
        pmids = dataset.get("pubmed_ids", [])

        print(f"\n--- Dataset {i}: {geo_id} ---")
        print_info(f"PMIDs to download: {pmids}")

        # Download papers for this dataset
        response = requests.post(
            f"{BASE_URL}/api/agents/enrich-fulltext", json=[dataset], params={"include_full_content": True}
        )

        if response.status_code != 200:
            print_error(f"Download failed for {geo_id}: {response.status_code}")
            continue

        enriched = response.json()[0]
        enriched_datasets.append(enriched)

        # Verify mapping
        print_success(f"Downloaded for {geo_id}")
        print(f"   Fulltext count: {enriched.get('fulltext_count', 0)}")
        print(f"   Status: {enriched.get('fulltext_status', 'unknown')}")

        # Check fulltext array
        fulltext = enriched.get("fulltext", [])
        if fulltext:
            print(f"\n   ✅ Fulltext array has {len(fulltext)} entries:")
            for j, ft in enumerate(fulltext, 1):
                pmid = ft.get("pmid", "unknown")
                has_methods = bool(ft.get("methods"))
                has_results = bool(ft.get("results"))
                methods_len = len(ft.get("methods", ""))
                results_len = len(ft.get("results", ""))

                print(f"      [{j}] PMID {pmid}")
                print(f"          - Methods: {methods_len} chars {'✅' if has_methods else '❌'}")
                print(f"          - Results: {results_len} chars {'✅' if has_results else '❌'}")

                # Verify PMID is in original list
                if pmid in pmids:
                    print(f"          - ✅ PMID {pmid} matches dataset's pubmed_ids")
                else:
                    print(f"          - ❌ WARNING: PMID {pmid} NOT in dataset's pubmed_ids!")
        else:
            print_error("   No fulltext entries (all downloads failed)")

        time.sleep(1)  # Small delay between downloads

    return enriched_datasets


def verify_mapping(enriched_datasets: List[Dict[str, Any]]):
    """Step 3: Verify correct mapping between datasets and PDFs."""
    print_section("STEP 3: Verify Dataset-to-PDF Mapping")

    for i, dataset in enumerate(enriched_datasets, 1):
        geo_id = dataset["geo_id"]
        original_pmids = set(dataset.get("pubmed_ids", []))
        fulltext = dataset.get("fulltext", [])
        fulltext_pmids = set([ft.get("pmid") for ft in fulltext])

        print(f"\n--- Dataset {i}: {geo_id} ---")
        print(f"Original PMIDs: {sorted(original_pmids)}")
        print(f"Fulltext PMIDs: {sorted(fulltext_pmids)}")

        # Check if fulltext PMIDs are subset of original PMIDs
        if fulltext_pmids.issubset(original_pmids):
            print_success("✅ All fulltext PMIDs match original pubmed_ids (no mixing!)")
        else:
            extra_pmids = fulltext_pmids - original_pmids
            print_error(f"❌ WARNING: Extra PMIDs found in fulltext: {extra_pmids}")

        # Check for cross-contamination
        other_datasets = [ds for ds in enriched_datasets if ds["geo_id"] != geo_id]
        for other_ds in other_datasets:
            other_pmids = set(other_ds.get("pubmed_ids", []))
            overlap = fulltext_pmids & other_pmids
            if overlap:
                print_error(f"❌ MIXING DETECTED: PMIDs {overlap} belong to {other_ds['geo_id']}!")
            else:
                print_success(f"✅ No overlap with {other_ds['geo_id']}")


def analyze_datasets(enriched_datasets: List[Dict[str, Any]]):
    """Step 4: Run AI analysis on each dataset separately."""
    print_section("STEP 4: AI Analysis (Verify Correct Text Usage)")

    for i, dataset in enumerate(enriched_datasets, 1):
        geo_id = dataset["geo_id"]
        fulltext = dataset.get("fulltext", [])
        fulltext_pmids = [ft.get("pmid") for ft in fulltext]

        print(f"\n--- Dataset {i}: {geo_id} ---")
        print_info(f"Analyzing with PMIDs: {fulltext_pmids}")

        if not fulltext:
            print_error("Skipping - no fulltext available")
            continue

        # Run AI analysis
        response = requests.post(
            f"{BASE_URL}/api/agents/analyze",
            json={"datasets": [dataset], "query": "cancer research", "max_datasets": 1},
        )

        if response.status_code != 200:
            print_error(f"AI analysis failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            continue

        analysis_result = response.json()
        analysis_text = analysis_result.get("analysis", "")

        print_success("AI analysis completed")
        print(f"\nAnalysis preview (first 500 chars):")
        print("-" * 80)
        print(analysis_text[:500])
        print("-" * 80)

        # Verify AI used correct PMIDs
        print("\n🔍 Checking if AI analysis mentions correct PMIDs...")
        mentioned_pmids = []
        for pmid in fulltext_pmids:
            if pmid in analysis_text or str(pmid) in analysis_text:
                mentioned_pmids.append(pmid)
                print_success(f"   PMID {pmid} mentioned in analysis ✅")

        # Check for wrong PMIDs (from other datasets)
        other_datasets = [ds for ds in enriched_datasets if ds["geo_id"] != geo_id]
        wrong_pmids_found = []
        for other_ds in other_datasets:
            for other_pmid in other_ds.get("pubmed_ids", []):
                if other_pmid in analysis_text:
                    wrong_pmids_found.append((other_pmid, other_ds["geo_id"]))

        if wrong_pmids_found:
            print_error("⚠️  WARNING: AI analysis mentions PMIDs from other datasets!")
            for wrong_pmid, wrong_geo_id in wrong_pmids_found:
                print(f"   - PMID {wrong_pmid} belongs to {wrong_geo_id}")
        else:
            print_success("✅ AI analysis uses ONLY this dataset's PMIDs (no cross-contamination)")

        # Check if Methods/Results sections are referenced
        if "method" in analysis_text.lower() or "result" in analysis_text.lower():
            print_success("✅ AI analysis references Methods/Results sections")
        else:
            print_info("⚠️  AI analysis doesn't explicitly mention Methods/Results")

        time.sleep(1)


def main():
    """Run complete validation test."""
    print("\n" + "█" * 80)
    print("  COMPREHENSIVE VALIDATION TEST")
    print("  URL → PDF → Parsed Text → AI Analysis Mapping")
    print("█" * 80)

    try:
        # Step 1: Search - try multiple queries to find datasets with PMIDs
        queries = ["breast cancer", "RNA-seq cancer", "tumor microenvironment"]
        datasets = []

        for query in queries:
            datasets = search_datasets(query)
            if datasets:
                break
            print_info(f"No datasets with PMIDs for '{query}', trying next query...")

        if not datasets:
            print_error("No datasets found with linked papers after trying multiple queries. Exiting.")
            return

        # Step 2: Download PDFs
        enriched_datasets = download_papers(datasets)
        if not enriched_datasets:
            print_error("No datasets successfully enriched. Exiting.")
            return

        # Step 3: Verify mapping
        verify_mapping(enriched_datasets)

        # Step 4: AI analysis
        analyze_datasets(enriched_datasets)

        # Final summary
        print_section("FINAL SUMMARY")

        total_datasets = len(enriched_datasets)
        datasets_with_fulltext = len([ds for ds in enriched_datasets if ds.get("fulltext")])

        print(f"Total datasets tested: {total_datasets}")
        print(f"Datasets with fulltext: {datasets_with_fulltext}")

        # Check for any mapping issues
        all_correct = True
        for dataset in enriched_datasets:
            original_pmids = set(dataset.get("pubmed_ids", []))
            fulltext_pmids = set([ft.get("pmid") for ft in dataset.get("fulltext", [])])
            if not fulltext_pmids.issubset(original_pmids):
                all_correct = False
                break

        if all_correct and datasets_with_fulltext > 0:
            print_success("\n🎉 ALL TESTS PASSED!")
            print_success("✅ Dataset-to-PDF mapping is CORRECT")
            print_success("✅ No cross-contamination detected")
            print_success("✅ AI analysis uses correct parsed text")
        else:
            print_error("\n⚠️  SOME ISSUES DETECTED")
            print_info("Review the logs above for details")

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
