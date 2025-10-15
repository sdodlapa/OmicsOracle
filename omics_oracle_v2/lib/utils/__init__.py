"""
Shared utilities and cross-pipeline components.

This module contains utilities that are used across multiple pipelines
and don't belong to any specific pipeline.

Components:
- UniversalIdentifier: Cross-pipeline publication identifier system
"""

from omics_oracle_v2.lib.utils.identifiers import (
    IdentifierMetadata, IdentifierType, UniversalIdentifier,
    get_identifier_from_filename, resolve_doi_from_filename)

__all__ = [
    "UniversalIdentifier",
    "IdentifierType",
    "IdentifierMetadata",
    "get_identifier_from_filename",
    "resolve_doi_from_filename",
]
