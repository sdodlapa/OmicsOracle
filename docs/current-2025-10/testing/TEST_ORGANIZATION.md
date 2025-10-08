# Test Organization - Phase 0 Task 5

**Status:** ✅ Complete
**Date:** 2025-01-02
**Branch:** phase-0-cleanup

## Overview

Task 5 organized the test structure to work with the new package import structure and enhanced test fixtures for better test development experience.

## Changes Made

### 1. Enhanced Test Configuration (conftest.py)

**File:** `tests/conftest.py`

**Improvements:**
- Comprehensive module docstring with fixture documentation
- Additional directory fixtures (test_data_dir)
- Test configuration fixture with safe defaults
- Mock environment variables fixture
- Service mock fixtures (NLP, cache, GEO client)
- Custom pytest markers configuration

**New Fixtures Added:**

#### Configuration Fixtures
- `test_config` - Test configuration with safe defaults (in-memory DB, disabled cache)
- `mock_env_vars` - Automatically sets up test environment variables

#### Service Mocks
- `mock_nlp_service` - Mocked NLP service with common methods
- `mock_cache` - Mocked cache with async get/set/delete methods
- `mock_geo_client` - Mocked GEO client with search/fetch methods

#### Directory Fixtures
- `test_data_dir` - Creates temporary test data directory

**Example Usage:**
```python
def test_with_fixtures(temp_dir, mock_geo_client, test_config):
    """Test uses multiple fixtures automatically."""
    # temp_dir is automatically created and cleaned up
    # mock_geo_client provides mocked GEO API responses
    # test_config provides safe configuration
    pass
```

### 2. Import Structure Cleanup

**Script:** `scripts/fix_test_imports.py`

Fixed outdated imports in test files:
- Changed `from src.omics_oracle.X` → `from omics_oracle.X`
- Changed `import src.omics_oracle.X` → `import omics_oracle.X`

**Files Fixed:** 18 test files
- tests/pipeline/test_initialization.py
- tests/unit/test_cache_disabling.py
- tests/unit/test_progress_callback_setup.py
- tests/unit/test_pipeline_status.py
- tests/integration/test_phase3_architecture.py
- tests/integration/test_search.py
- tests/integration/test_geo_client.py
- tests/e2e/test_search_pipeline.py
- And 10 more files

### 3. Sys Import Cleanup

**Script:** `scripts/organize_tests_phase0.py`

Analyzed test structure and removed unnecessary sys imports:
- **Total test files:** 88
- **Test files by category:** unit (20), integration (42), e2e (2), performance (3), security (6), others
- **Unnecessary sys imports removed:** 1
- **Legitimate sys imports kept:** 30 (for sys.exit, sys.executable, etc.)

**Legitimate sys Usage Examples:**
- sys.exit - for test runners and CLI tests
- sys.executable - for subprocess tests
- sys.modules - for module mocking
- sys.path mocking - for import testing

### 4. Custom Test Markers

Added custom markers to pytest configuration:

```python
@pytest.mark.unit          # Fast unit tests, no external dependencies
@pytest.mark.integration   # Integration tests, may require services
@pytest.mark.e2e          # End-to-end tests, full system
@pytest.mark.slow         # Slow-running tests
@pytest.mark.requires_api_key    # Tests requiring API keys
@pytest.mark.requires_network    # Tests requiring network access
```

**Usage:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests that don't require network
pytest -m "not requires_network"
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # 20 unit test files
│   ├── integrations/        # Integration library tests
│   └── test_*.py           # Fast, isolated tests
├── integration/             # 42 integration test files
│   └── test_*.py           # Tests with external dependencies
├── e2e/                     # 2 end-to-end test files
│   └── test_*.py           # Full system tests
├── performance/             # 3 performance test files
├── security/                # 6 security test files
├── geo_tools/              # 1 GEO client test
├── pipeline/               # 1 pipeline test
├── validation/             # 1 validation test
├── interface/              # 4 interface tests
├── browser/                # 1 browser test
├── mobile/                 # 1 mobile test
└── system/                 # 1 system test
```

## Test Categories

### Unit Tests (tests/unit/)
- **Purpose:** Fast, isolated tests with no external dependencies
- **Characteristics:**
  - Use mocks for all external services
  - Test individual functions/classes
  - Complete in milliseconds
- **Run with:** `pytest tests/unit/ -m unit`

### Integration Tests (tests/integration/)
- **Purpose:** Test component interactions
- **Characteristics:**
  - May require external services (database, cache, APIs)
  - Test data flow between components
  - May be slower than unit tests
- **Run with:** `pytest tests/integration/ -m integration`

### E2E Tests (tests/e2e/)
- **Purpose:** Test complete user workflows
- **Characteristics:**
  - Full system testing
  - May require all services running
  - Slowest tests
- **Run with:** `pytest tests/e2e/ -m e2e`

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest tests/

# Run specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with markers
pytest -m unit                    # Only unit tests
pytest -m "unit and not slow"     # Fast unit tests
pytest -m "not requires_network"  # Tests without network

# Run with coverage
pytest tests/unit/ --cov=src/omics_oracle --cov-report=html

# Run specific test file
pytest tests/unit/test_cache_disabling.py

# Run specific test function
pytest tests/unit/test_cache_disabling.py::test_cache_disabled

# Verbose output
pytest -v tests/unit/

# Show print statements
pytest -s tests/unit/
```

### CI/CD Recommendations

```bash
# Fast CI (PR checks)
pytest tests/unit/ -m "unit and not slow" --maxfail=3

# Full CI (main branch)
pytest tests/ --cov=src/omics_oracle --cov-report=xml --maxfail=5

# Integration CI (scheduled)
pytest tests/integration/ -m "integration and not requires_api_key"
```

## Known Issues & Workarounds

### Issue 1: Import Errors in Some Tests
**Status:** Partially resolved
**Cause:** Some test files import from old module paths or non-existent modules
**Impact:** 5 test files have collection errors
**Workaround:** These tests need individual fixes (separate from bulk cleanup)

**Affected Files:**
- tests/unit/integrations/test_citation_managers.py
- tests/unit/integrations/test_pubmed_integration.py
- tests/unit/test_pipeline_status.py (ProgressEvent import)
- tests/unit/test_progress_callback_setup.py (ProgressEvent import)
- tests/unit/test_request_validation.py (interfaces module)

**Resolution Plan:** Address in future tasks when refactoring those specific modules

### Issue 2: Some Tests Require External Services
**Status:** By design
**Solution:** Use markers to skip in CI

```bash
# Skip tests requiring external services
pytest -m "not requires_api_key and not requires_network"
```

## Benefits

### For Developers
- **Better Fixtures:** Comprehensive shared fixtures reduce boilerplate
- **Clear Organization:** Test categories are well-defined
- **Easier Debugging:** Enhanced fixtures include better docstrings
- **Flexible Running:** Markers allow selective test execution

### For CI/CD
- **Faster Feedback:** Unit tests can run quickly for PRs
- **Selective Testing:** Run different test suites at different stages
- **Better Reporting:** Clear test categorization

### For Maintenance
- **Consistent Imports:** All tests use proper package imports
- **Shared Fixtures:** Changes to common test setup happen in one place
- **Clear Dependencies:** Markers indicate test requirements

## Verification

### Test Collection
```bash
# Verify pytest can collect tests
python -m pytest tests/ --collect-only -q

# Results:
# - 93+ tests collected
# - 5 known import errors (to be fixed individually)
# - All other tests collect successfully
```

### Import Structure
```bash
# Verify no src.omics_oracle imports remain
grep -r "from src\.omics_oracle" tests/
# Should return 0 results

# Verify proper imports
grep -r "from omics_oracle" tests/ | wc -l
# Should show many results
```

### Fixtures Work
```python
# Verify fixtures are available
pytest --fixtures tests/

# Should show all new fixtures:
# - test_config
# - mock_env_vars
# - mock_nlp_service
# - mock_cache
# - mock_geo_client
```

## Migration Guide for Test Writers

### Old Style (Before Task 5)
```python
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.omics_oracle.pipeline import OmicsOracle

def test_something():
    # Manual setup
    config = {"debug": True}
    pipeline = OmicsOracle(config)
    # Test code...
```

### New Style (After Task 5)
```python
from omics_oracle.pipeline import OmicsOracle

def test_something(test_config, mock_cache):
    # Fixtures provided automatically
    pipeline = OmicsOracle(test_config)
    pipeline.cache = mock_cache
    # Test code...
```

### Using Markers
```python
import pytest
from omics_oracle.geo_tools import UnifiedGEOClient

@pytest.mark.unit
def test_geo_client_init(mock_geo_client):
    """Fast unit test with mock."""
    assert mock_geo_client is not None

@pytest.mark.integration
@pytest.mark.requires_network
async def test_geo_client_real():
    """Integration test requiring network."""
    client = UnifiedGEOClient()
    result = await client.search("BRCA1")
    assert result is not None
```

## Next Steps

**Task 6 - Documentation (Day 9):**
- Update README with Phase 0 changes
- Create cleanup summary document
- Document architectural decisions
- Update migration guides

## References

- **pytest documentation:** https://docs.pytest.org/
- **pytest markers:** https://docs.pytest.org/en/stable/example/markers.html
- **pytest fixtures:** https://docs.pytest.org/en/stable/fixture.html
- **Task 5 Plan:** See CODEBASE_CLEANUP_PLAN.md Section 2.5

## Files Modified

1. `tests/conftest.py` - Enhanced with comprehensive fixtures
2. 18 test files - Fixed import structure
3. `scripts/organize_tests_phase0.py` - Test analysis script
4. `scripts/fix_test_imports.py` - Import fixing script
5. `docs/TEST_ORGANIZATION.md` - This documentation

## Scripts Created

1. **organize_tests_phase0.py** - Analyzes test structure and removes unnecessary imports
2. **fix_test_imports.py** - Fixes src.omics_oracle → omics_oracle imports

---
**Phase 0 Progress:** Task 5 of 7 Complete ✅
