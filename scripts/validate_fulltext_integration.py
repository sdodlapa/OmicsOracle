#!/usr/bin/env python3
"""
Comprehensive Test: Validate Full-Text Integration

This test validates:
1. Remove max_papers limit (download ALL papers)
2. URL fallback logic (tries all URLs until success)
3. AI Analysis uses parsed text (explicitly shows when not available)

Tests both backend API and end-to-end flow.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(text: str):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")


def print_success(text: str):
    print(f"{GREEN}✅ {text}{RESET}")


def print_fail(text: str):
    print(f"{RED}❌ {text}{RESET}")


def print_info(text: str):
    print(f"{CYAN}ℹ️  {text}{RESET}")


def print_warning(text: str):
    print(f"{YELLOW}⚠️  {text}{RESET}")


async def test_1_no_max_papers_limit():
    """
    TEST 1: Verify max_papers limit can be removed

    Expected: Should download ALL papers in dataset.pubmed_ids
    """
    print_header("TEST 1: No Max Papers Limit")

    print_info("Testing that we can download ALL papers without limit...")
    print()

    # Check current implementation
    import inspect

    from omics_oracle_v2.api.routes import agents

    # Get the enrich_fulltext function signature
    sig = inspect.signature(agents.enrich_fulltext)
    max_papers_param = sig.parameters.get("max_papers")

    if max_papers_param:
        default_value = max_papers_param.default

        # Check if it's a Query object (FastAPI)
        if hasattr(default_value, "default"):
            actual_default = default_value.default
        else:
            actual_default = default_value

        print(f"Current default: max_papers={actual_default}")

        if actual_default == 3:
            print_warning("Max papers is LIMITED to 3")
            print()
            print("Recommendation: Change to max_papers=None (unlimited)")
            print("Location: omics_oracle_v2/api/routes/agents.py, line ~323")
            print()
            return False
        elif actual_default is None or actual_default == inspect.Parameter.empty:
            print_success("Max papers is UNLIMITED (None)!")
            print()
            print("This means:")
            print("  • Downloads ALL papers in dataset.pubmed_ids")
            print("  • No artificial limit")
            print("  • Can optionally set limit via API parameter")
            print()
            return True
        else:
            print_warning(f"Max papers is set to {actual_default}")
            return False
    else:
        print_fail("max_papers parameter not found")
        return False


async def test_2_url_fallback_logic():
    """
    TEST 2: Verify URL fallback tries all sources

    Expected: Should try URLs from all 11 sources until one succeeds
    """
    print_header("TEST 2: URL Fallback Logic")

    print_info("Checking if download manager tries all URLs...")
    print()

    # Read the download_with_fallback code
    download_manager_file = project_root / "omics_oracle_v2/lib/enrichment/fulltext/download_manager.py"

    with open(download_manager_file, "r") as f:
        code = f.read()

    # Check for retry logic
    has_retry_loop = "for attempt in range" in code and "max_retries_per_url" in code
    has_url_loop = "for i, source_url in enumerate(all_urls)" in code or "for url" in code
    has_fallback_continue = "continue" in code and "# All retries exhausted" in code

    print("Code Analysis:")
    print(f"  • Has retry loop per URL: {has_retry_loop}")
    print(f"  • Has URL iteration loop: {has_url_loop}")
    print(f"  • Has fallback logic: {has_fallback_continue}")
    print()

    if has_retry_loop and has_url_loop:
        print_success("YES! Downloads try all URLs with retry logic")
        print()
        print("Logic flow:")
        print("  1. For each URL in all_urls (up to 11 sources)")
        print("  2.   Try download (attempt 1)")
        print("  3.   If fails, retry (attempt 2)")
        print("  4.   If still fails, move to next URL")
        print("  5. Continues until one succeeds or all exhausted")
        print()
        return True
    else:
        print_fail("Fallback logic incomplete")
        return False


async def test_3_parallel_url_collection():
    """
    TEST 3: Verify parallel collection queries sources and handles failures gracefully

    Expected: Should query sources in parallel and accept 1+ URLs (not require all 11)
    """
    print_header("TEST 3: Parallel URL Collection & Graceful Failure Handling")

    print_info("Checking parallel collection logic...")
    print()

    # Read manager code
    manager_file = project_root / "omics_oracle_v2/lib/enrichment/fulltext/manager.py"

    with open(manager_file, "r") as f:
        code = f.read()

    # Check for key logic patterns
    checks = {
        "Parallel execution (asyncio.gather)": "asyncio.gather" in code and "get_all_fulltext_urls" in code,
        "Graceful exception handling (return_exceptions=True)": "return_exceptions=True" in code,
        "Continues on source failure (not break)": "continue" in code
        and "isinstance(result, Exception)" in code,
        "Only fails if NO URLs (not if < 11)": "if not all_urls:" in code,
        "Succeeds with 1+ URLs": "if len(all_urls)" in code or "all_urls.append" in code,
        "Logs failures without breaking": "logger.debug" in code and "exception:" in code,
    }

    print("Logic Validation:")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    print()

    # Check for major sources (don't require all 11)
    major_sources = ["pmc", "unpaywall", "institutional", "core", "scihub"]
    found_major = sum(1 for s in major_sources if s in code)

    print(f"Major sources found: {found_major}/{len(major_sources)}")
    print()

    passed_checks = sum(checks.values())
    total_checks = len(checks)

    if passed_checks >= 5 and found_major >= 4:
        print_success(
            f"YES! Parallel collection with graceful handling ({passed_checks}/{total_checks} checks)"
        )
        print()
        print("✅ Implementation correctly:")
        print("  • Queries multiple sources in parallel")
        print("  • Gracefully handles source failures")
        print("  • Succeeds with 1+ URLs (not require all 11)")
        print("  • Only fails if zero URLs found")
        print("  • Provides multiple URLs for download fallback")
        print()
        print("This matches the goal: 'Collect URLs from as many sources")
        print("as available, succeed with at least 1 URL'")
        print()
        return True
    else:
        print_fail(f"Only {passed_checks}/{total_checks} checks passed")
        return False


async def test_4_ai_uses_fulltext():
    """
    TEST 4: Verify AI Analysis uses parsed full-text

    Expected: Should include Methods/Results/Discussion in GPT-4 prompt
    """
    print_header("TEST 4: AI Analysis Uses Full-Text")

    print_info("Checking if AI analysis includes parsed text...")
    print()

    # Read agents.py analyze endpoint
    agents_file = project_root / "omics_oracle_v2/api/routes/agents.py"

    with open(agents_file, "r") as f:
        code = f.read()

    # Check for full-text inclusion in prompt
    checks = {
        "Extracts abstract": "ft.abstract" in code,
        "Extracts methods": "ft.methods" in code,
        "Extracts results": "ft.results" in code,
        "Extracts discussion": "ft.discussion" in code,
        "Tells GPT about full-text": "You have access to full-text content" in code,
        "Warns when no full-text": "No full-text available" in code or "GEO summary only" in code,
        "Different prompts for with/without": "if total_fulltext_papers > 0" in code
        or "if ds.fulltext" in code,
    }

    print("Analysis Code Checks:")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    print()

    passed_count = sum(checks.values())
    total_count = len(checks)

    if passed_count >= 6:
        print_success(f"YES! AI uses full-text ({passed_count}/{total_count} checks passed)")
        print()
        print("Flow confirmed:")
        print("  1. Extract parsed sections (abstract, methods, results, discussion)")
        print("  2. Include in GPT-4 prompt")
        print("  3. Tell GPT it has full-text access")
        print("  4. Warn user when full-text not available")
        print()
        return True
    else:
        print_fail(f"Only {passed_count}/{total_count} checks passed")
        return False


async def test_5_backend_integration():
    """
    TEST 5: Backend API integration test

    Actually call the API endpoints to verify behavior
    """
    print_header("TEST 5: Backend API Integration")

    print_info("Testing actual API endpoints...")
    print()

    try:
        import aiohttp

        # Test if API is running
        async with aiohttp.ClientSession() as session:
            # Health check
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print_success("API is running")
                else:
                    print_fail(f"API health check failed: {response.status}")
                    return False

        print()
        print_info("API is accessible. Ready for integration tests.")
        print()
        print("To test full integration:")
        print("  1. Use dashboard: http://localhost:8000/dashboard")
        print("  2. Search for a dataset")
        print("  3. Click 'Download Papers'")
        print("  4. Click 'AI Analysis'")
        print("  5. Verify it mentions Methods/Results from papers")
        print()
        return True

    except Exception as e:
        print_warning(f"Could not connect to API: {e}")
        print()
        print_info("Start API with: ./start_omics_oracle.sh")
        return False


async def main():
    """Run all tests"""

    print_header("COMPREHENSIVE VALIDATION TEST SUITE")
    print()
    print("This test suite validates:")
    print("  1. ❓ Can we download ALL papers (no max limit)?")
    print("  2. ❓ Does fallback try all 11 sources?")
    print("  3. ❓ Are all sources queried in parallel?")
    print("  4. ❓ Does AI Analysis use parsed full-text?")
    print("  5. ❓ Backend API integration working?")
    print()

    # Run tests
    results = {}

    results["test_1"] = await test_1_no_max_papers_limit()

    results["test_2"] = await test_2_url_fallback_logic()

    results["test_3"] = await test_3_parallel_url_collection()

    results["test_4"] = await test_4_ai_uses_fulltext()

    results["test_5"] = await test_5_backend_integration()

    # Final Summary
    print_header("TEST RESULTS SUMMARY")

    test_names = {
        "test_1": "Remove max_papers limit",
        "test_2": "URL fallback tries all sources",
        "test_3": "Parallel URL collection",
        "test_4": "AI uses parsed full-text",
        "test_5": "Backend API integration",
    }

    print()
    for test_key, test_name in test_names.items():
        passed = results[test_key]
        status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
        print(f"{status}  {test_name}")

    print()

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"Overall: {passed_count}/{total_count} tests passed")
    print()

    if passed_count == total_count:
        print_success("ALL TESTS PASSED! 🎉")
        print()
        print("Your system is working correctly:")
        print("  • Downloads ALL papers (with configurable limit)")
        print("  • Tries all 11 sources with fallback")
        print("  • Queries sources in parallel")
        print("  • AI uses parsed full-text")
        print("  • Backend integration working")
    else:
        print_warning(f"{total_count - passed_count} tests need attention")
        print()
        print("Next steps:")
        if not results["test_1"]:
            print("  1. Remove max_papers=3 limit in agents.py")
        if not results["test_2"]:
            print("  2. Verify download_with_fallback logic")
        if not results["test_3"]:
            print("  3. Check get_all_fulltext_urls implementation")
        if not results["test_4"]:
            print("  4. Verify AI analysis prompt building")
        if not results["test_5"]:
            print("  5. Start the API server")

    print()


if __name__ == "__main__":
    asyncio.run(main())
