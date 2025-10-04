"""
Agent execution context and message models.

Provides data models for agent communication, state management,
and execution context.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of messages agents can exchange."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"
    RESULT = "result"


class AgentMessage(BaseModel):
    """
    Message passed between agents.

    Represents a single communication between agents with metadata
    for routing, priority, and error handling.
    """

    message_id: str = Field(..., description="Unique message identifier")
    message_type: MessageType = Field(..., description="Type of message")
    sender: str = Field(..., description="Agent that sent the message")
    recipient: Optional[str] = Field(None, description="Target agent (None for broadcast)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When message was created")
    parent_id: Optional[str] = Field(None, description="ID of message this responds to")
    priority: int = Field(default=0, ge=0, le=10, description="Message priority (0-10)")

    class Config:
        frozen = False


class AgentContext(BaseModel):
    """
    Context for agent execution.

    Maintains state, messages, and metadata for a single agent's
    execution within a workflow.
    """

    agent_name: str = Field(..., description="Name of the agent")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")
    state: Dict[str, Any] = Field(default_factory=dict, description="Agent state variables")
    messages: List[AgentMessage] = Field(default_factory=list, description="Messages sent/received")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")

    class Config:
        frozen = False

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the context."""
        self.messages.append(message)

    def add_error(self, error: str) -> None:
        """Add an error to the context."""
        self.errors.append(error)

    def set_metric(self, key: str, value: Any) -> None:
        """Set a performance metric."""
        self.metrics[key] = value

    def get_duration_ms(self) -> Optional[float]:
        """Get execution duration in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None


class ExecutionContext(BaseModel):
    """
    Context for multi-agent workflow execution.

    Coordinates multiple agents and maintains global state for
    the entire workflow execution.
    """

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_name: str = Field(..., description="Name of the workflow being executed")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Workflow start time")
    end_time: Optional[datetime] = Field(None, description="Workflow end time")
    agent_contexts: Dict[str, AgentContext] = Field(
        default_factory=dict, description="Context for each agent"
    )
    global_state: Dict[str, Any] = Field(default_factory=dict, description="Shared workflow state")
    messages: List[AgentMessage] = Field(default_factory=list, description="All workflow messages")
    success: bool = Field(default=True, description="Whether workflow succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        frozen = False

    def get_or_create_agent_context(self, agent_name: str) -> AgentContext:
        """Get or create context for an agent."""
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = AgentContext(agent_name=agent_name)
        return self.agent_contexts[agent_name]

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the workflow context."""
        self.messages.append(message)

        # Also add to sender's context
        if message.sender in self.agent_contexts:
            self.agent_contexts[message.sender].add_message(message)

    def set_global_state(self, key: str, value: Any) -> None:
        """Set a global state variable."""
        self.global_state[key] = value

    def get_global_state(self, key: str, default: Any = None) -> Any:
        """Get a global state variable."""
        return self.global_state.get(key, default)

    def get_duration_ms(self) -> Optional[float]:
        """Get total workflow duration in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None

    def finish(self, success: bool = True, error: Optional[str] = None) -> None:
        """Mark workflow as finished."""
        self.end_time = datetime.utcnow()
        self.success = success
        self.error = error

        # Mark all agent contexts as finished
        for context in self.agent_contexts.values():
            if context.end_time is None:
                context.end_time = self.end_time
