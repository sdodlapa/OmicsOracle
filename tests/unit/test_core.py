"""
Basic unit tests for OmicsOracle core modules.

This module provides basic unit tests to ensure core functionality
and prevent workflow failures.
"""

import unittest
from pathlib import Path

# Add the src directory to the path to import our modules


class TestCoreModules(unittest.TestCase):
    """Test basic functionality of core modules."""

    def test_import_modules(self) -> None:
        """Test that core modules can be imported."""
        try:
            # Import after path setup to avoid E402
            import omics_oracle.core.config  # noqa: F401
            import omics_oracle.core.exceptions  # noqa: F401
            import omics_oracle.core.models  # noqa: F401
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")


if __name__ == "__main__":
    unittest.main()
