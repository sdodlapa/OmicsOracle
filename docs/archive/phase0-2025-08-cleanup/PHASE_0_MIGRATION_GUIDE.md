# Phase 0 Migration Guide

**For Developers Working with OmicsOracle Post-Phase 0 Cleanup**

This guide helps you migrate your development environment and code to work with the Phase 0 cleanup changes.

## Quick Migration Checklist

- [ ] Pull latest phase-0-cleanup branch
- [ ] Re-install package: `pip install -e .`
- [ ] Update imports (remove sys.path manipulations)
- [ ] Use new API endpoints (prefer v2 over v1)
- [ ] Update tests to use shared fixtures
- [ ] Run tests with new markers

## Installation Changes

### Before Phase 0
```bash
# Old way - install from requirements.txt
pip install -r requirements.txt
```

### After Phase 0
```bash
# New way - install as editable package
pip install -e .

# Optional: Install additional dependencies
pip install -r requirements-web.txt  # For web interface
pip install -r requirements-dev.txt  # For development
```

**Why?** Phase 0 cleanup modernized the package structure. Installing with `-e` flag enables:
- Proper import resolution without sys.path manipulation
- Type checking support (PEP 561)
- IDE autocomplete and code intelligence
- Changes reflected immediately without reinstallation

## Import Changes

### Before Phase 0
```python
# ❌ Old style - manual sys.path manipulation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from omics_oracle.pipeline import OmicsOracle
from omics_oracle.core.config import Config
```

### After Phase 0
```python
# ✅ New style - clean imports
from omics_oracle.pipeline import OmicsOracle
from omics_oracle.core.config import Config
```

**Why?** The package is now properly installed, so Python's import system can find it automatically.

### Common Import Patterns

```python
# Pipeline
from omics_oracle.pipeline import OmicsOracle, QueryResult, QueryStatus

# Core utilities
from omics_oracle.core import Config, get_logger, OmicsOracleException
from omics_oracle.core.models import SearchRequest, GEOSeries

# Services
from omics_oracle.services import SummarizationService, CostManager

# GEO tools
from omics_oracle.geo_tools import UnifiedGEOClient

# NLP
from omics_oracle.nlp import PromptInterpreter, BiomedicalNER

# Search
from omics_oracle.search import AdvancedSearchEnhancer
```

## API Endpoint Changes

### Before Phase 0
```bash
# Mixed endpoint organization
POST http://localhost:8000/search
GET  http://localhost:8000/health
POST http://localhost:8000/enhanced-search
```

### After Phase 0
```bash
# Clear v1/v2 separation

# v1 API (maintenance mode, use only if needed)
POST http://localhost:8000/api/v1/search
GET  http://localhost:8000/api/v1/analyze

# v2 API (recommended for new development)
POST http://localhost:8000/api/v2/search
POST http://localhost:8000/api/v2/realtime/search
GET  http://localhost:8000/api/v2/ai/summary

# Health endpoints (unversioned)
GET  http://localhost:8000/health
GET  http://localhost:8000/health/ready
GET  http://localhost:8000/health/live

# UI endpoints
GET  http://localhost:8000/
GET  http://localhost:8000/dashboard
```

**Why?** Clear API versioning allows:
- Independent evolution of API versions
- Gradual deprecation of old endpoints
- Better API documentation
- Load balancer compatibility (health endpoints)

### Deprecation Timeline

- **v1 API**: Maintenance mode, deprecated April 2026
- **v2 API**: Active development, recommended for all new work

### Client Code Update

```python
# Before Phase 0
import requests
response = requests.post("http://localhost:8000/search", json={"query": "BRCA1"})

# After Phase 0 - use v2
response = requests.post("http://localhost:8000/api/v2/search", json={"query": "BRCA1"})
```

## Test Writing Changes

### Before Phase 0
```python
# ❌ Old style - manual setup in each test
def test_something():
    config = {
        "debug": True,
        "cache": {"enabled": False},
        "database": {"url": "sqlite:///:memory:"}
    }
    mock_cache = MagicMock()
    mock_cache.get = AsyncMock(return_value=None)

    # Test code...
```

### After Phase 0
```python
# ✅ New style - use shared fixtures
import pytest
from omics_oracle.pipeline import OmicsOracle

@pytest.mark.unit
def test_something(test_config, mock_cache, mock_geo_client):
    """Test uses shared fixtures automatically."""
    pipeline = OmicsOracle(test_config)
    # Fixtures provide everything you need
    # Test code...
```

### Available Fixtures

**Configuration:**
- `test_config` - Safe test configuration (in-memory DB, cache disabled)
- `mock_env_vars` - Mocked environment variables

**Directories:**
- `temp_dir` - Temporary directory (auto-cleanup)
- `test_data_dir` - Test data directory
- `sample_data_dir` - Sample data path

**Mock Services:**
- `mock_nlp_service` - Mocked NLP service with common methods
- `mock_cache` - Mocked cache with get/set/delete
- `mock_geo_client` - Mocked GEO client with search/fetch

**Sample Data:**
- `mock_geo_response` - Sample GEO API response
- `sample_fasta_content` - Sample FASTA sequences
- `sample_metadata` - Sample metadata structure

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_fast_unit():
    """Fast unit test, no external dependencies."""
    pass

@pytest.mark.integration
def test_with_services():
    """Integration test, may need services."""
    pass

@pytest.mark.slow
def test_long_running():
    """Slow test, only run when needed."""
    pass

@pytest.mark.requires_network
async def test_real_api():
    """Test requiring network access."""
    pass

@pytest.mark.requires_api_key
async def test_with_api():
    """Test requiring API keys."""
    pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run by marker
pytest -m unit                    # Fast unit tests only
pytest -m integration             # Integration tests
pytest -m "not slow"              # Skip slow tests
pytest -m "not requires_network"  # Skip network tests

# Run specific category
pytest tests/unit/                # Unit tests directory
pytest tests/integration/         # Integration tests directory

# Run with coverage
pytest --cov=src/omics_oracle --cov-report=html
```

## Type Checking

Phase 0 added PEP 561 support, enabling type checking:

### Enable Type Checking

```bash
# Install mypy
pip install mypy

# Run type checking
mypy src/omics_oracle/

# Check specific file
mypy src/omics_oracle/pipeline/pipeline.py
```

### Type Hints Example

```python
from typing import Optional, List
from omics_oracle.pipeline import OmicsOracle, QueryResult
from omics_oracle.core.models import SearchRequest

def process_query(
    oracle: OmicsOracle,
    query: str,
    limit: Optional[int] = None
) -> List[QueryResult]:
    """Type checkers now understand these types."""
    request = SearchRequest(query=query, limit=limit or 10)
    results = oracle.search(request)
    return results
```

## IDE Configuration

### VS Code

Update `.vscode/settings.json`:

```json
{
  "python.analysis.extraPaths": [],
  "python.autoComplete.extraPaths": [],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ]
}
```

**Note:** Remove any `extraPaths` that point to `src/` - the package is now properly installed.

### PyCharm

1. Mark `src/` as "Sources Root" ❌ **NOT NEEDED ANYMORE**
2. Instead, ensure package is installed: `pip install -e .` ✅
3. Configure test runner: Settings → Tools → Python Integrated Tools → Testing → pytest

## Common Migration Issues

### Issue 1: ImportError after pulling changes

**Symptom:**
```
ImportError: No module named 'omics_oracle'
```

**Solution:**
```bash
# Reinstall package in development mode
pip install -e .
```

### Issue 2: Tests fail with import errors

**Symptom:**
```
ModuleNotFoundError: No module named 'src.omics_oracle'
```

**Solution:**
Update test imports to remove `src.` prefix:
```python
# Before
from src.omics_oracle.pipeline import OmicsOracle

# After
from omics_oracle.pipeline import OmicsOracle
```

### Issue 3: API endpoints return 404

**Symptom:**
```
404 Not Found: POST /search
```

**Solution:**
Update to use versioned endpoints:
```python
# Before
requests.post("http://localhost:8000/search")

# After
requests.post("http://localhost:8000/api/v2/search")
```

### Issue 4: Type checking doesn't work

**Symptom:**
```
mypy: error: Skipping analyzing "omics_oracle": module is installed, but missing library stubs
```

**Solution:**
Verify py.typed exists after reinstallation:
```bash
pip install -e .
python -c "import omics_oracle, os; print(os.path.exists(os.path.join(os.path.dirname(omics_oracle.__file__), 'py.typed')))"
# Should print: True
```

## Git Workflow

### Working with phase-0-cleanup branch

```bash
# Pull latest changes
git checkout phase-0-cleanup
git pull origin phase-0-cleanup

# Create feature branch from phase-0-cleanup
git checkout -b feature/my-feature

# After making changes, reinstall package
pip install -e .

# Run tests
pytest -m unit

# Commit changes
git add .
git commit -m "feat: my feature"
```

### Pre-commit Hooks

Phase 0 uses selective hook skipping:

```bash
# Commit with selective hooks
SKIP=ascii-only-enforcer,no-emoji-check,flake8 git commit -m "Your message"

# Or set it globally for the session
export SKIP=ascii-only-enforcer,no-emoji-check,flake8
git commit -m "Your message"
```

**Why?** Some hooks are temporarily skipped for existing code. They'll be re-enabled after addressing legacy issues.

## Documentation Updates

All Phase 0 changes are documented:

1. **[PHASE_0_CLEANUP_SUMMARY.md](PHASE_0_CLEANUP_SUMMARY.md)** - Complete cleanup summary
2. **[PACKAGE_STRUCTURE.md](PACKAGE_STRUCTURE.md)** - Package organization details
3. **[ROUTE_CONSOLIDATION.md](ROUTE_CONSOLIDATION.md)** - API route organization
4. **[TEST_ORGANIZATION.md](TEST_ORGANIZATION.md)** - Test structure guide
5. **[README.md](../README.md)** - Updated with Phase 0 info

## Getting Help

If you encounter issues after migrating:

1. Check this migration guide first
2. Review [PHASE_0_CLEANUP_SUMMARY.md](PHASE_0_CLEANUP_SUMMARY.md)
3. Check specific topic docs (PACKAGE_STRUCTURE.md, etc.)
4. Search existing issues on GitHub
5. Ask in team chat or create a new issue

## Quick Reference

### Installation
```bash
pip install -e .  # Always run after pulling changes
```

### Imports
```python
from omics_oracle.module import Something  # No sys.path needed
```

### API Endpoints
```bash
# Use v2 API
http://localhost:8000/api/v2/*
```

### Tests
```bash
pytest -m unit  # Fast unit tests
```

### Type Checking
```bash
mypy src/omics_oracle/
```

---

**Updated:** October 2, 2025
**Phase:** Phase 0 Cleanup (5 of 7 tasks complete)
**Branch:** phase-0-cleanup
