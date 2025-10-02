"""
OmicsOracle v2 - Multi-Agent Smart Data Summary System.

A modern, clean architecture for biomedical data analysis with multi-agent capabilities.
This version features extracted, reusable algorithms with proper dependency injection
and comprehensive testing.

Main Components:
    - lib.nlp: Biomedical NER and text processing
    - lib.geo: GEO database access and parsing
    - lib.ai: AI-powered summarization services
    - core: Configuration and infrastructure

Example:
    >>> from omics_oracle_v2.lib.nlp import BiomedicalNER
    >>> ner = BiomedicalNER()
    >>> result = ner.extract_entities("TP53 gene mutations in lung cancer")
    >>> print(result.entities)

Version: 2.0.0
Status: Development (Phase 1: Algorithm Extraction)
"""

__version__ = "2.0.0-alpha"
__author__ = "OmicsOracle Team"

# Public API exports will be added as modules are implemented
__all__ = []
