"""
Agent-specific exceptions.

Provides a hierarchy of exceptions for agent-related errors,
extending the base OmicsOracle exception hierarchy.
"""

from ..core.exceptions import OmicsOracleError


class AgentError(OmicsOracleError):
    """Base exception for all agent-related errors."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class AgentStateError(AgentError):
    """Raised when agent state is invalid."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    pass


class AgentValidationError(AgentError):
    """Raised when agent input/output validation fails."""

    pass


class AgentCommunicationError(AgentError):
    """Raised when inter-agent communication fails."""

    pass
