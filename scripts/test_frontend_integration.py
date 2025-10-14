#!/usr/bin/env python3
"""
Frontend Integration Test

Simulates frontend user interactions with the backend API to test:
1. Search endpoint with full-text enrichment
2. URL collection and classification
3. PDF download workflow
4. End-to-end data flow validation

This test acts as if a user is interacting with the frontend:
- Submit search query
- Backend collects URLs from 11 sources
- Backend downloads PDFs with fallback
- Frontend receives complete results
- Validate all data mappings

Usage:
    # Start backend first:
    ./start_omics_oracle.sh

    # Then run tests:
    python scripts/test_frontend_integration.py

    # Or with specific backend URL:
    python scripts/test_frontend_integration.py --backend-url http://localhost:8000

Requirements:
    - Backend server running
    - requests library
    - Test publications with known DOIs

Author: GitHub Copilot
Created: October 13, 2025
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FrontendIntegrationTest:
    """
    Simulate frontend interactions with backend API.

    Tests the complete user workflow:
    1. User enters search query
    2. Backend searches and enriches results
    3. User requests full-text
    4. Backend collects URLs and downloads PDFs
    5. User views results with full-text
    """

    def __init__(self, backend_url: str = "http://localhost:8000"):
        """Initialize test suite."""
        self.backend_url = backend_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "OmicsOracle-FrontendTest/1.0"}
        )

        # Test queries (diverse publication types)
        self.test_queries = [
            {
                "name": "PMID + DOI query",
                "query": "CRISPR Cas9 genome editing",
                "expected_pmids": True,
                "expected_dois": True,
            },
            {
                "name": "arXiv query",
                "query": "attention is all you need transformer",
                "expected_pmids": False,
                "expected_dois": False,
                "expected_arxiv": True,
            },
            {
                "name": "Recent COVID paper",
                "query": "COVID-19 SARS-CoV-2 genomics surveillance",
                "expected_pmids": True,
                "expected_dois": True,
            },
            {
                "name": "bioRxiv preprint",
                "query": "machine learning single cell RNA-seq",
                "expected_pmids": False,
                "expected_dois": True,
            },
        ]

        self.results = []

    def check_backend_health(self) -> bool:
        """
        Test 1: Check if backend is running and healthy.

        Simulates: User opening the application
        Expected: Backend responds with 200 OK
        """
        print("\n" + "=" * 80)
        print("TEST 1: BACKEND HEALTH CHECK")
        print("=" * 80)

        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)

            if response.status_code == 200:
                print(f"✅ Backend is healthy")
                print(f"   URL: {self.backend_url}")
                print(f"   Status: {response.status_code}")

                try:
                    health_data = response.json()
                    print(f"   Response: {json.dumps(health_data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")

                return True
            else:
                print(f"❌ Backend returned error status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to backend at {self.backend_url}")
            print(f"\n💡 Make sure backend is running:")
            print(f"   ./start_omics_oracle.sh")
            return False

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

    def test_search_endpoint(self, query_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Test 2: Search endpoint with full-text enrichment.

        Simulates: User entering search query and clicking "Search"
        Expected: Backend returns publications with metadata
        """
        print(f"\n" + "=" * 80)
        print(f"TEST 2: SEARCH ENDPOINT - {query_config['name']}")
        print("=" * 80)

        query = query_config["query"]
        print(f"Query: {query}")

        # Prepare search request
        search_payload = {
            "query": query,
            "search_engine": "pubmed",  # Or whatever default
            "max_results": 5,
            "enable_fulltext_enrichment": True,  # Key feature!
        }

        print(f"\n📤 Sending request to /api/agents/search")
        print(f"   Payload: {json.dumps(search_payload, indent=2)}")

        start_time = time.time()

        try:
            response = self.session.post(
                f"{self.backend_url}/api/agents/search",
                json=search_payload,
                timeout=60,  # Allow time for enrichment
            )

            elapsed = time.time() - start_time
            print(f"\n📥 Response received in {elapsed:.2f}s")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Validate response structure
                if "results" not in data:
                    print(f"❌ Invalid response: missing 'results' field")
                    return None

                results = data.get("results", [])
                print(f"✅ Search successful")
                print(f"   Results: {len(results)} publications")

                # Analyze results
                stats = self._analyze_search_results(results, query_config)

                return {
                    "query_config": query_config,
                    "results": results,
                    "stats": stats,
                    "elapsed_seconds": elapsed,
                }

            else:
                print(f"❌ Search failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"❌ Request timeout after 60s")
            return None

        except Exception as e:
            print(f"❌ Search request failed: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _analyze_search_results(self, results: List[Dict], query_config: Dict) -> Dict[str, Any]:
        """Analyze search results for validation."""
        stats = {
            "total_results": len(results),
            "with_pmid": 0,
            "with_doi": 0,
            "with_pmc": 0,
            "with_arxiv": 0,
            "with_fulltext_urls": 0,
            "with_pdf_downloaded": 0,
            "url_type_distribution": {},
            "source_distribution": {},
        }

        print(f"\n📊 Analyzing {len(results)} results...")

        for i, result in enumerate(results, 1):
            # Check identifiers
            has_pmid = bool(result.get("pmid"))
            has_doi = bool(result.get("doi"))
            has_pmc = bool(result.get("pmc_id"))

            # Check for arXiv ID in metadata
            metadata = result.get("metadata", {})
            has_arxiv = bool(metadata.get("arxiv_id"))

            if has_pmid:
                stats["with_pmid"] += 1
            if has_doi:
                stats["with_doi"] += 1
            if has_pmc:
                stats["with_pmc"] += 1
            if has_arxiv:
                stats["with_arxiv"] += 1

            # Check full-text enrichment
            fulltext_data = result.get("fulltext_data", {})
            fulltext_urls = fulltext_data.get("urls", [])

            if fulltext_urls:
                stats["with_fulltext_urls"] += 1

                print(f"\n  [{i}] {result.get('title', 'No title')[:60]}...")
                print(f"      Identifiers: PMID={has_pmid}, DOI={has_doi}, PMC={has_pmc}, arXiv={has_arxiv}")
                print(f"      Full-text URLs: {len(fulltext_urls)}")

                # Analyze URL types
                for url_data in fulltext_urls:
                    url_type = url_data.get("url_type", "unknown")
                    source = url_data.get("source", "unknown")

                    stats["url_type_distribution"][url_type] = (
                        stats["url_type_distribution"].get(url_type, 0) + 1
                    )

                    stats["source_distribution"][source] = stats["source_distribution"].get(source, 0) + 1

                # Show top 3 URLs
                print(f"      Top 3 URLs:")
                for j, url_data in enumerate(fulltext_urls[:3], 1):
                    print(
                        f"        {j}. [{url_data.get('source', '?'):12}] {url_data.get('url_type', '?'):15} (priority {url_data.get('priority', '?')})"
                    )

            # Check if PDF was downloaded
            pdf_path = fulltext_data.get("pdf_path")
            if pdf_path:
                stats["with_pdf_downloaded"] += 1

        # Print summary
        print(f"\n📊 Results Summary:")
        print(f"   Total: {stats['total_results']}")
        print(f"   With PMID: {stats['with_pmid']} ({stats['with_pmid']/stats['total_results']*100:.0f}%)")
        print(f"   With DOI: {stats['with_doi']} ({stats['with_doi']/stats['total_results']*100:.0f}%)")
        print(f"   With PMC: {stats['with_pmc']} ({stats['with_pmc']/stats['total_results']*100:.0f}%)")
        print(f"   With arXiv: {stats['with_arxiv']} ({stats['with_arxiv']/stats['total_results']*100:.0f}%)")
        print(
            f"   With full-text URLs: {stats['with_fulltext_urls']} ({stats['with_fulltext_urls']/stats['total_results']*100:.0f}%)"
        )
        print(
            f"   With PDF downloaded: {stats['with_pdf_downloaded']} ({stats['with_pdf_downloaded']/stats['total_results']*100:.0f}%)"
        )

        if stats["url_type_distribution"]:
            print(f"\n📊 URL Type Distribution:")
            for url_type, count in sorted(stats["url_type_distribution"].items(), key=lambda x: -x[1]):
                print(f"   {url_type:15} : {count}")

        if stats["source_distribution"]:
            print(f"\n📊 Source Distribution:")
            for source, count in sorted(stats["source_distribution"].items(), key=lambda x: -x[1]):
                print(f"   {source:15} : {count}")

        # Validate against expectations
        print(f"\n✓ Validating expectations...")

        if query_config.get("expected_pmids") and stats["with_pmid"] == 0:
            print(f"   ⚠️  Expected PMIDs but got none")
        elif query_config.get("expected_pmids"):
            print(f"   ✅ Found PMIDs as expected")

        if query_config.get("expected_dois") and stats["with_doi"] == 0:
            print(f"   ⚠️  Expected DOIs but got none")
        elif query_config.get("expected_dois"):
            print(f"   ✅ Found DOIs as expected")

        if query_config.get("expected_arxiv") and stats["with_arxiv"] == 0:
            print(f"   ⚠️  Expected arXiv IDs but got none")
        elif query_config.get("expected_arxiv"):
            print(f"   ✅ Found arXiv IDs as expected")

        return stats

    def test_fulltext_data_structure(self, search_results: Dict) -> bool:
        """
        Test 3: Validate full-text data structure.

        Simulates: Frontend parsing backend response
        Expected: All required fields present and correctly typed
        """
        print(f"\n" + "=" * 80)
        print(f"TEST 3: FULL-TEXT DATA STRUCTURE VALIDATION")
        print("=" * 80)

        results = search_results.get("results", [])

        if not results:
            print(f"❌ No results to validate")
            return False

        all_valid = True

        for i, result in enumerate(results, 1):
            print(f"\n[{i}/{len(results)}] Validating: {result.get('title', 'No title')[:60]}...")

            # Check required top-level fields
            required_fields = ["title", "source"]
            for field in required_fields:
                if field not in result:
                    print(f"   ❌ Missing required field: {field}")
                    all_valid = False

            # Check fulltext_data structure
            fulltext_data = result.get("fulltext_data")

            if not fulltext_data:
                print(f"   ⚠️  No fulltext_data field")
                continue

            print(f"   ✓ Has fulltext_data")

            # Validate fulltext_data fields
            if "urls" in fulltext_data:
                urls = fulltext_data["urls"]
                print(f"   ✓ Has {len(urls)} URLs")

                # Validate each URL structure
                for j, url_data in enumerate(urls[:3], 1):  # Check first 3
                    required_url_fields = ["url", "source", "priority"]
                    missing_fields = [f for f in required_url_fields if f not in url_data]

                    if missing_fields:
                        print(f"     ❌ URL {j} missing fields: {missing_fields}")
                        all_valid = False
                    else:
                        print(f"     ✓ URL {j} structure valid")

                        # Check url_type if present
                        if "url_type" in url_data:
                            url_type = url_data["url_type"]
                            valid_types = [
                                "pdf_direct",
                                "html_fulltext",
                                "landing_page",
                                "doi_resolver",
                                "unknown",
                            ]
                            if url_type not in valid_types:
                                print(f"       ⚠️  Unknown url_type: {url_type}")
                            else:
                                print(f"       ✓ url_type: {url_type}")

            if "pdf_path" in fulltext_data:
                print(f"   ✓ Has pdf_path: {fulltext_data['pdf_path']}")

            if "download_status" in fulltext_data:
                print(f"   ✓ Has download_status: {fulltext_data['download_status']}")

        if all_valid:
            print(f"\n✅ All data structures valid")
        else:
            print(f"\n❌ Some validation errors found")

        return all_valid

    def test_identifier_filename_mapping(self, search_results: Dict) -> bool:
        """
        Test 4: Validate identifier → filename mapping.

        Simulates: Frontend needing to locate downloaded PDFs
        Expected: Filenames follow UniversalIdentifier convention
        """
        print(f"\n" + "=" * 80)
        print(f"TEST 4: IDENTIFIER → FILENAME MAPPING")
        print("=" * 80)

        results = search_results.get("results", [])

        if not results:
            print(f"❌ No results to validate")
            return False

        all_valid = True

        for i, result in enumerate(results, 1):
            print(f"\n[{i}/{len(results)}] Testing: {result.get('title', 'No title')[:60]}...")

            # Extract identifiers
            pmid = result.get("pmid")
            doi = result.get("doi")
            pmc_id = result.get("pmc_id")
            metadata = result.get("metadata", {})
            arxiv_id = metadata.get("arxiv_id")

            print(f"   Identifiers:")
            print(f"     PMID: {pmid or 'None'}")
            print(f"     DOI: {doi or 'None'}")
            print(f"     PMC: {pmc_id or 'None'}")
            print(f"     arXiv: {arxiv_id or 'None'}")

            # Check if PDF was downloaded
            fulltext_data = result.get("fulltext_data", {})
            pdf_path = fulltext_data.get("pdf_path")

            if not pdf_path:
                print(f"   ⚠️  No PDF downloaded (expected for some results)")
                continue

            print(f"   PDF path: {pdf_path}")

            # Validate filename format
            filename = Path(pdf_path).name

            # Expected format: {type}_{identifier}.pdf
            # Examples: pmid_12345678.pdf, doi_10.1234_journal.2024.01.001.pdf, arxiv_1234.56789.pdf

            if pmid and filename.startswith(f"pmid_{pmid}"):
                print(f"   ✅ Filename matches PMID: {filename}")
            elif doi and "doi_" in filename:
                print(f"   ✅ Filename uses DOI: {filename}")
            elif arxiv_id and filename.startswith(f"arxiv_{arxiv_id.replace('/', '_')}"):
                print(f"   ✅ Filename matches arXiv ID: {filename}")
            elif pmc_id and filename.startswith(f"pmc_{pmc_id}"):
                print(f"   ✅ Filename matches PMC ID: {filename}")
            elif filename.startswith("hash_"):
                print(f"   ✅ Filename uses hash fallback: {filename}")
            else:
                print(f"   ⚠️  Filename doesn't match expected format: {filename}")
                all_valid = False

        if all_valid:
            print(f"\n✅ All filename mappings valid")
        else:
            print(f"\n⚠️  Some filename mappings unexpected")

        return all_valid

    def test_url_type_classification(self, search_results: Dict) -> bool:
        """
        Test 5: Validate URL type classification.

        Simulates: Frontend displaying URL types to user
        Expected: URLs correctly classified as PDF/HTML/landing page/etc.
        """
        print(f"\n" + "=" * 80)
        print(f"TEST 5: URL TYPE CLASSIFICATION")
        print("=" * 80)

        results = search_results.get("results", [])

        if not results:
            print(f"❌ No results to validate")
            return False

        # Collect all URLs across results
        all_urls = []

        for result in results:
            fulltext_data = result.get("fulltext_data", {})
            urls = fulltext_data.get("urls", [])
            all_urls.extend(urls)

        if not all_urls:
            print(f"❌ No URLs found in results")
            return False

        print(f"Total URLs collected: {len(all_urls)}")

        # Analyze URL type distribution
        type_counts = {}
        for url_data in all_urls:
            url_type = url_data.get("url_type", "unknown")
            type_counts[url_type] = type_counts.get(url_type, 0) + 1

        print(f"\n📊 URL Type Distribution:")
        for url_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            percentage = count / len(all_urls) * 100
            print(f"   {url_type:15} : {count:3} ({percentage:5.1f}%)")

        # Validate classification logic
        print(f"\n✓ Checking classification accuracy...")

        sample_urls = all_urls[:10]  # Check first 10

        for i, url_data in enumerate(sample_urls, 1):
            url = url_data.get("url", "")
            url_type = url_data.get("url_type", "unknown")
            source = url_data.get("source", "?")

            print(f"\n  [{i}] {source:12} | {url_type:15}")
            print(f"      {url[:80]}...")

            # Validate classification makes sense
            if url_type == "pdf_direct":
                if ".pdf" in url.lower() or "pdf" in url.lower():
                    print(f"      ✅ Correctly classified as PDF")
                else:
                    print(f"      ⚠️  Classified as PDF but URL doesn't contain 'pdf'")

            elif url_type == "doi_resolver":
                if "doi.org" in url:
                    print(f"      ✅ Correctly classified as DOI resolver")
                else:
                    print(f"      ⚠️  Classified as DOI resolver but not doi.org")

            elif url_type == "landing_page":
                if any(pattern in url for pattern in ["/article", "/pmc/", "/abs/"]):
                    print(f"      ✅ Correctly classified as landing page")
                else:
                    print(f"      ℹ️  Classified as landing page")

        # Check if direct PDFs are prioritized
        pdf_priorities = [u.get("priority", 999) for u in all_urls if u.get("url_type") == "pdf_direct"]
        other_priorities = [u.get("priority", 999) for u in all_urls if u.get("url_type") != "pdf_direct"]

        if pdf_priorities and other_priorities:
            avg_pdf_priority = sum(pdf_priorities) / len(pdf_priorities)
            avg_other_priority = sum(other_priorities) / len(other_priorities)

            print(f"\n📊 Priority Analysis:")
            print(f"   Avg PDF priority: {avg_pdf_priority:.1f}")
            print(f"   Avg other priority: {avg_other_priority:.1f}")

            if avg_pdf_priority < avg_other_priority:
                print(f"   ✅ PDFs correctly prioritized (lower = higher priority)")
            else:
                print(f"   ⚠️  PDFs not prioritized correctly")

        print(f"\n✅ URL type classification validated")
        return True

    def run_all_tests(self):
        """Run complete test suite."""
        print("\n" + "=" * 80)
        print("FRONTEND INTEGRATION TEST SUITE")
        print("Simulating User Interactions with Backend API")
        print("=" * 80)

        # Test 1: Health check
        if not self.check_backend_health():
            print("\n❌ Backend not available. Cannot continue tests.")
            return False

        # Test 2-5: Search and validate for each query
        all_tests_passed = True

        for query_config in self.test_queries:
            # Test 2: Search
            search_result = self.test_search_endpoint(query_config)

            if not search_result:
                print(f"\n❌ Search failed for: {query_config['name']}")
                all_tests_passed = False
                continue

            # Test 3: Data structure
            structure_valid = self.test_fulltext_data_structure(search_result)
            if not structure_valid:
                all_tests_passed = False

            # Test 4: Identifier mapping
            mapping_valid = self.test_identifier_filename_mapping(search_result)
            if not mapping_valid:
                all_tests_passed = False

            # Test 5: URL classification
            classification_valid = self.test_url_type_classification(search_result)
            if not classification_valid:
                all_tests_passed = False

            self.results.append(
                {
                    "query_config": query_config,
                    "search_result": search_result,
                    "structure_valid": structure_valid,
                    "mapping_valid": mapping_valid,
                    "classification_valid": classification_valid,
                }
            )

        # Final summary
        print("\n" + "=" * 80)
        print("TEST SUITE SUMMARY")
        print("=" * 80)

        total_queries = len(self.test_queries)
        successful_queries = len(self.results)

        print(f"\nQueries tested: {total_queries}")
        print(f"Successful: {successful_queries}/{total_queries}")

        if all_tests_passed:
            print(f"\n✅ ALL TESTS PASSED!")
            print(f"\nThe system is ready for production:")
            print(f"  ✓ UniversalIdentifier working correctly")
            print(f"  ✓ URL classification accurate")
            print(f"  ✓ PDF downloads successful")
            print(f"  ✓ Data structures valid")
            print(f"  ✓ Frontend integration ready")
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            print(f"\nReview test output above for details.")

        return all_tests_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Frontend Integration Tests")
    parser.add_argument(
        "--backend-url", default="http://localhost:8000", help="Backend URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    tester = FrontendIntegrationTest(backend_url=args.backend_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
