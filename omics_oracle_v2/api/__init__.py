"""
OmicsOracle v2 Agent API

RESTful API for the multi-agent biomedical research platform.
"""

# Lazy import to avoid circular dependencies
# Use: from omics_oracle_v2.api.main import create_app
__all__ = ["create_app"]


def __getattr__(name):
    """Lazy-load create_app to avoid circular imports."""
    if name == "create_app":
        from omics_oracle_v2.api.main import create_app
        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
