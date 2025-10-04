"""
Presentation Layer for OmicsOracle

This layer contains all user interfaces including:

Interfaces:
    - Web: FastAPI-based REST API and web dashboard
    - CLI: Command-line interface for scripting and automation
    - API: Programmatic API endpoints

The presentation layer follows the clean architecture pattern,
depending only on the core domain and service layers.

Example:
    >>> from omics_oracle.presentation.web import create_app
    >>> app = create_app()
"""

__version__ = "0.1.0"

# Note: Presentation layer modules are not directly exported
# Import from submodules as needed:
# - omics_oracle.presentation.web for FastAPI application
# - omics_oracle.presentation.cli for command-line interface
# - omics_oracle.presentation.api for API utilities

__all__ = []
