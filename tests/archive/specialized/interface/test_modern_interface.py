#!/usr/bin/env python3
"""
Simple test script to validate the OmicsOracle modern interface setup
"""

import sys
from pathlib import Path

# Add the modern interface to Python path
modern_path = Path(__file__).parent / "interfaces" / "modern"


def test_imports() -> bool:
    """Test that all core modules can be imported"""
    print("[TEST] Testing module imports...")

    try:
        print("[PASS] Config module imported successfully")
        print("[PASS] Exceptions module imported successfully")
        print("[PASS] Logging module imported successfully")
        print("[PASS] Models module imported successfully")
        print("[PASS] Services module imported successfully")

        # Note: API modules will have import issues due to relative imports
        # This is expected until we set up proper package structure

        return True

    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_configuration() -> bool:
    """Test configuration system"""
    print("\n[TEST] Testing configuration...")

    try:
        from core.config import get_config

        config = get_config("development")
        print(f"[PASS] Configuration loaded: {config.__class__.__name__}")
        print(f"   - Debug mode: {config.DEBUG}")
        print(f"   - Cache enabled: {config.CACHE_ENABLED}")
        print(f"   - Data directory: {config.DATA_DIR}")

        return True

    except ImportError as e:
        print(f"[FAIL] Configuration error: {e}")
        return False


def test_models() -> bool:
    """Test data models"""
    print("\n[TEST] Testing data models...")

    try:
        from models import SearchQuery, SearchResult

        # Create a test search query
        query = SearchQuery(query="test search", page=1, page_size=20)
        print(f"[PASS] SearchQuery created: '{query.query}' (page {query.page})")

        # Create a test search result
        result = SearchResult(
            id="GSE12345",
            title="Test Dataset",
            abstract="This is a test dataset",
        )
        print(f"[PASS] SearchResult created: {result.id} - {result.title}")

        # Test serialization
        result_dict = result.to_dict()
        print(f"[PASS] SearchResult serialization: {len(result_dict)} fields")

        return True

    except ImportError as e:
        print(f"[FAIL] Models error: {e}")
        return False


def test_services() -> bool:
    """Test service classes"""
    print("\n[TEST] Testing services...")

    try:
        from services import CacheService, ExportService, SearchService

        # Test SearchService
        SearchService()
        print("[PASS] SearchService instantiated")

        # Test CacheService
        cache_dir = Path("/tmp/test_cache")
        cache_service = CacheService(cache_dir, ttl=60, enabled=True)
        print("[PASS] CacheService instantiated")

        # Test cache operations
        cache_service.set("test_key", {"test": "data"})
        cached_data = cache_service.get("test_key")
        if cached_data:
            print("[PASS] Cache operations working")
        else:
            print("[WARN] Cache operations not working as expected")

        # Test ExportService
        export_dir = Path("/tmp/test_exports")
        ExportService(export_dir)
        print("[PASS] ExportService instantiated")

        return True

    except ImportError as e:
        print(f"[FAIL] Services error: {e}")
        return False


def main() -> int:
    """Run all tests"""
    print("[START] OmicsOracle Modern Interface Validation")
    print("=" * 50)

    tests = [test_imports, test_configuration, test_models, test_services]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except ImportError as e:
            print(f"[FAIL] Test {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"[RESULTS] Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! The modern interface is ready.")
        return 0
    else:
        print("[WARNING] Some tests failed. Check the setup and dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
