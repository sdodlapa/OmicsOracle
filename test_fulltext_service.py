#!/usr/bin/env python3
"""
Quick validation script for FulltextService implementation.

Tests:
1. Service can be instantiated
2. Methods exist and have correct signatures
3. No import errors

Does NOT test actual functionality (requires running server).
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from omics_oracle_v2.api.models import DatasetResponse
        from omics_oracle_v2.services.fulltext_service import FulltextService

        print("  [OK] Imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False


def test_service_instantiation():
    """Test that service can be instantiated."""
    print("\nTesting service instantiation...")
    try:
        from omics_oracle_v2.services.fulltext_service import FulltextService

        service = FulltextService()
        print("  [OK] Service instantiated")

        # Check that db is set
        if hasattr(service, "db"):
            print("  [OK] Database registry accessible")
        else:
            print("  [FAIL] Database registry missing")
            return False

        return True
    except Exception as e:
        print(f"  [FAIL] Instantiation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_method_signatures():
    """Test that required methods exist."""
    print("\nTesting method signatures...")
    try:
        import inspect

        from omics_oracle_v2.services.fulltext_service import FulltextService

        service = FulltextService()

        # Check main method
        if hasattr(service, "enrich_datasets"):
            sig = inspect.signature(service.enrich_datasets)
            print(f"  [OK] enrich_datasets method exists")
            print(f"     Parameters: {list(sig.parameters.keys())}")
        else:
            print("  [FAIL] enrich_datasets method missing")
            return False

        # Check helper methods
        helper_methods = [
            "_process_dataset",
            "_fetch_publications",
            "_collect_urls",
            "_download_pdfs",
            "_parse_pdfs",
        ]

        for method_name in helper_methods:
            if hasattr(service, method_name):
                print(f"  [OK] {method_name} exists")
            else:
                print(f"  [FAIL] {method_name} missing")
                return False

        return True
    except Exception as e:
        print(f"  [FAIL] Method check failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_async_compatibility():
    """Test that async methods are properly defined."""
    print("\nTesting async compatibility...")
    try:
        import inspect

        from omics_oracle_v2.services.fulltext_service import FulltextService

        service = FulltextService()

        # Check that enrich_datasets is async
        if inspect.iscoroutinefunction(service.enrich_datasets):
            print("  [OK] enrich_datasets is async")
        else:
            print("  [FAIL] enrich_datasets is not async")
            return False

        # Check helper methods are async
        async_methods = [
            "_process_dataset",
            "_fetch_publications",
            "_collect_urls",
            "_download_pdfs",
            "_parse_pdfs",
        ]

        for method_name in async_methods:
            method = getattr(service, method_name)
            if inspect.iscoroutinefunction(method):
                print(f"  [OK] {method_name} is async")
            else:
                print(f"  [FAIL] {method_name} is not async")
                return False

        return True
    except Exception as e:
        print(f"  [FAIL] Async check failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("FULLTEXT SERVICE VALIDATION")
    print("=" * 80)

    tests = [
        ("Imports", test_imports),
        ("Instantiation", test_service_instantiation),
        ("Method Signatures", test_method_signatures),
        ("Async Compatibility", lambda: asyncio.run(test_async_compatibility())),
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n[OK] All validation tests passed!")
        print("\nNext steps:")
        print("1. Restart server: ./start_omics_oracle.sh")
        print("2. Search for GSE570")
        print("3. Click 'Download Papers'")
        print("4. Verify PDFs download to data/pdfs/GSE570/")
        return 0
    else:
        print("\n[FAIL] Some tests failed - fix before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
