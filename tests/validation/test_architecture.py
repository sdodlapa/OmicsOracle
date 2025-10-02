#!/usr/bin/env python3
"""
Test script for Phase 1.2 Core Architecture Implementation.

This script validates our core architecture components:
- Configuration system
- Exception handling
- Data models
- Logging infrastructure
"""

import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent.parent / "src"


def test_configuration() -> bool:
    """Test configuration system."""
    print("Testing configuration system...")

    try:
        from omics_oracle.core.config import ConfigManager

        # Test configuration manager
        config_manager = ConfigManager()
        print("  [SQRT] ConfigManager instantiated successfully")

        # Test loading development config
        config = config_manager.load_config("development")
        print(f"  [SQRT] Development config loaded: {config.environment}")
        print(f"  [SQRT] Database URL: {config.database.url}")
        print(f"  [SQRT] Logging level: {config.logging.level}")

        return True
    except Exception as e:
        print(f"  X Configuration test failed: {e}")
        return False


def test_exceptions() -> bool:
    """Test exception hierarchy."""
    print("Testing exception system...")

    try:
        from omics_oracle.core.exceptions import ConfigurationError, OmicsOracleException

        # Test base exception
        try:
            raise OmicsOracleException("Test exception", code="TEST_ERROR")
        except OmicsOracleException as e:
            print(f"  [SQRT] Base exception: {e.message} (code: {e.code})")

        # Test specific exception
        try:
            raise ConfigurationError("Config error")
        except ConfigurationError as e:
            print(f"  [SQRT] Configuration exception: {e.message}")

        return True
    except Exception as e:
        print(f"  X Exception test failed: {e}")
        return False


def test_models():
    """Test data models."""
    print("Testing data models...")

    try:
        from omics_oracle.core.models import AssayType, GEOSample, SearchRequest

        # Test enum
        assay = AssayType.RNA_SEQ
        print(f"  [SQRT] AssayType enum: {assay}")

        # Test dataclass
        sample = GEOSample(accession="GSM123456", title="Test sample", organism="Homo sapiens")
        print(f"  [SQRT] GEOSample created: {sample.accession}")

        # Test Pydantic model
        request = SearchRequest(query="RNA-seq human")
        print(f"  [SQRT] SearchRequest created: {request.query}")

        return True
    except Exception as e:
        print(f"  X Models test failed: {e}")
        return False


def test_logging():
    """Test logging system."""
    print("Testing logging system...")

    try:
        from omics_oracle.core.logging import get_logger, setup_logging

        # Test setup
        setup_logging(level="DEBUG")
        print("  [SQRT] Logging setup successful")

        # Test logger
        logger = get_logger("test")
        logger.info("Test log message")
        print("  [SQRT] Logger created and message logged")

        return True
    except Exception as e:
        print(f"  X Logging test failed: {e}")
        return False


def test_integration():
    """Test integration between components."""
    print("Testing component integration...")

    try:
        # Test that we can load config and use it in other components
        from omics_oracle.core.config import load_config
        from omics_oracle.core.models import SearchRequest

        # Load config (should work)
        config = load_config("development")
        print(f"  [SQRT] Config loaded for environment: {config.environment}")

        # Create a request model
        request = SearchRequest(query="test query")
        print(f"  [SQRT] Request model created: {request.query}")

        # Test validation error
        try:
            SearchRequest(query="")  # Should fail validation
        except Exception as e:
            print(f"  [SQRT] Validation error caught: {e}")

        return True
    except Exception as e:
        print(f"  X Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("[DNA] OmicsOracle Phase 1.2 Architecture Test")
    print("=" * 50)

    tests = [
        test_configuration,
        test_exceptions,
        test_models,
        test_logging,
        test_integration,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"  X Test failed with exception: {e}")
            results.append(False)
            print()

    # Summary
    passed = sum(results)
    total = len(results)

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[STATUS] All tests passed! Core architecture is ready.")
        return 0
    else:
        print("[STATUS][STATUS][STATUS] Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
