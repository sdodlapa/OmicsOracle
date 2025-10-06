"""
RAG (Retrieval-Augmented Generation) module for OmicsOracle.

This module provides components for combining semantic search with
large language model generation to produce natural language answers.
"""

from omics_oracle_v2.lib.rag.pipeline import Citation, LLMProvider, RAGConfig, RAGPipeline, RAGResponse

__all__ = [
    "RAGPipeline",
    "RAGConfig",
    "RAGResponse",
    "Citation",
    "LLMProvider",
]
