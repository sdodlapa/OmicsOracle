"""
Vector database for semantic search.

Provides vector storage and similarity search using FAISS.
"""

from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB
from omics_oracle_v2.lib.vector_db.interface import VectorDB

__all__ = ["VectorDB", "FAISSVectorDB"]
