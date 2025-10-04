"""
Shared pytest fixtures and configuration for OmicsOracle v2 tests.

Provides reusable fixtures for common test scenarios, mock objects,
and test data.
"""

from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_biomedical_text() -> str:
    """Return sample biomedical text for testing."""
    return (
        "The TP53 gene encodes a tumor suppressor protein that regulates "
        "cell cycle and apoptosis. Mutations in TP53 are commonly found "
        "in various cancers including lung cancer and breast cancer."
    )


@pytest.fixture
def sample_geo_accession() -> str:
    """Return a known stable GEO accession for testing."""
    return "GSE10000"  # Known stable dataset


# Additional fixtures will be added as modules are implemented
