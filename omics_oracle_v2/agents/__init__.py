"""
OmicsOracle v2 Agent Framework.

Provides a flexible multi-agent system for biomedical research workflows.
Agents collaborate to handle complex queries from natural language input
to comprehensive research reports.

Agent Types:
    - QueryAgent: Natural language query processing with NLP
    - SearchAgent: GEO database search and retrieval
    - DataAgent: Metadata extraction and validation
    - ReportAgent: AI-powered report generation
    - Orchestrator: Multi-agent workflow coordination

Example:
    >>> from omics_oracle_v2.agents import Orchestrator
    >>> from omics_oracle_v2.core import Settings
    >>>
    >>> settings = Settings()
    >>> orchestrator = Orchestrator(settings)
    >>> result = orchestrator.execute("Find TP53 breast cancer datasets")
    >>> print(result.report.summary)
"""

from .base import Agent, AgentResult, AgentState
from .context import AgentContext, ExecutionContext
from .exceptions import AgentError, AgentExecutionError, AgentStateError, AgentTimeoutError
from .query_agent import QueryAgent
from .search_agent import SearchAgent

__all__ = [
    # Base classes
    "Agent",
    "AgentResult",
    "AgentState",
    # Context
    "AgentContext",
    "ExecutionContext",
    # Exceptions
    "AgentError",
    "AgentExecutionError",
    "AgentStateError",
    "AgentTimeoutError",
    # Agents
    "QueryAgent",
    "SearchAgent",
]
