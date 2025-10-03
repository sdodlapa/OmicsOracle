"""
Base agent framework.

Provides abstract base classes for all agents in the multi-agent system.
Agents follow a standard lifecycle and communication protocol.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from ..core.config import Settings
from .context import AgentContext, AgentMessage, ExecutionContext, MessageType
from .exceptions import AgentExecutionError, AgentStateError, AgentValidationError

logger = logging.getLogger(__name__)

# Type variable for agent input/output
TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class AgentState(str, Enum):
    """Agent execution states."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentResult(BaseModel, Generic[TOutput]):
    """
    Result from agent execution.

    Encapsulates the output from an agent along with metadata
    about the execution.
    """

    agent_name: str = Field(..., description="Name of the agent that produced this result")
    state: AgentState = Field(..., description="Final state of the agent")
    output: Optional[TOutput] = Field(None, description="Agent output data")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def success(self) -> bool:
        """Whether the agent execution was successful."""
        return self.state == AgentState.COMPLETED and self.output is not None


class Agent(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for all agents.

    Defines the standard interface and lifecycle for agents in the
    multi-agent system. All concrete agents must implement the abstract
    methods.

    Lifecycle:
        1. __init__: Create agent with settings
        2. initialize: Set up resources, validate configuration
        3. execute: Process input and produce output
        4. cleanup: Release resources

    Example:
        >>> class MyAgent(Agent[MyInput, MyOutput]):
        ...     def _validate_input(self, input_data):
        ...         return input_data
        ...
        ...     def _process(self, input_data, context):
        ...         # Implementation
        ...         return MyOutput(...)
        ...
        >>> agent = MyAgent(settings)
        >>> result = agent.execute(MyInput(...))
    """

    def __init__(self, settings: Settings, agent_name: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            settings: Application settings
            agent_name: Optional custom name for the agent (defaults to class name)
        """
        self.settings = settings
        self.agent_name = agent_name or self.__class__.__name__
        self.state = AgentState.IDLE
        self._context: Optional[AgentContext] = None
        self._initialized = False

        logger.info(f"Agent '{self.agent_name}' created")

    @property
    def context(self) -> Optional[AgentContext]:
        """Get the current execution context."""
        return self._context

    def initialize(self) -> None:
        """
        Initialize the agent.

        Sets up any required resources, validates configuration,
        and prepares the agent for execution.

        Raises:
            AgentStateError: If agent is already initialized
            AgentExecutionError: If initialization fails
        """
        if self._initialized:
            raise AgentStateError(f"Agent '{self.agent_name}' is already initialized")

        try:
            self.state = AgentState.INITIALIZING
            logger.info(f"Initializing agent '{self.agent_name}'")

            self._initialize_resources()

            self.state = AgentState.READY
            self._initialized = True
            logger.info(f"Agent '{self.agent_name}' initialized successfully")

        except Exception as e:
            self.state = AgentState.FAILED
            error_msg = f"Failed to initialize agent '{self.agent_name}': {e}"
            logger.error(error_msg)
            raise AgentExecutionError(error_msg) from e

    def execute(
        self,
        input_data: TInput,
        execution_context: Optional[ExecutionContext] = None,
    ) -> AgentResult[TOutput]:
        """
        Execute the agent with the given input.

        Args:
            input_data: Input data for the agent
            execution_context: Optional execution context for workflow coordination

        Returns:
            AgentResult with output or error information

        Raises:
            AgentStateError: If agent is not ready
            AgentValidationError: If input validation fails
            AgentExecutionError: If execution fails
        """
        # Ensure initialized
        if not self._initialized:
            self.initialize()

        if self.state not in (AgentState.READY, AgentState.COMPLETED):
            raise AgentStateError(f"Agent '{self.agent_name}' is not ready (state: {self.state})")

        # Create or get agent context
        if execution_context:
            self._context = execution_context.get_or_create_agent_context(self.agent_name)
        else:
            self._context = AgentContext(agent_name=self.agent_name)

        start_time = datetime.utcnow()
        self.state = AgentState.RUNNING

        try:
            logger.info(f"Agent '{self.agent_name}' starting execution")

            # Validate input
            validated_input = self._validate_input(input_data)

            # Send start message
            if execution_context:
                self._send_message(
                    execution_context,
                    MessageType.STATUS,
                    {"status": "started", "input": validated_input.model_dump()},
                )

            # Process
            output = self._process(validated_input, self._context)

            # Validate output
            validated_output = self._validate_output(output)

            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000

            self.state = AgentState.COMPLETED
            self._context.end_time = end_time
            self._context.set_metric("execution_time_ms", execution_time)

            # Send completion message
            if execution_context:
                self._send_message(
                    execution_context,
                    MessageType.RESULT,
                    {"output": validated_output.model_dump() if validated_output else None},
                )

            logger.info(f"Agent '{self.agent_name}' completed successfully in {execution_time:.2f}ms")

            return AgentResult(
                agent_name=self.agent_name,
                state=self.state,
                output=validated_output,
                execution_time_ms=execution_time,
                metadata=self._context.metrics,
            )

        except AgentValidationError as e:
            self.state = AgentState.FAILED
            error_msg = f"Validation error in agent '{self.agent_name}': {e}"
            logger.error(error_msg)
            self._context.add_error(error_msg)

            if execution_context:
                self._send_message(execution_context, MessageType.ERROR, {"error": error_msg})

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.agent_name,
                state=self.state,
                output=None,
                error=error_msg,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            self.state = AgentState.FAILED
            error_msg = f"Execution error in agent '{self.agent_name}': {e}"
            logger.error(error_msg)
            self._context.add_error(error_msg)

            if execution_context:
                self._send_message(execution_context, MessageType.ERROR, {"error": error_msg})

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.agent_name,
                state=self.state,
                output=None,
                error=error_msg,
                execution_time_ms=execution_time,
            )

    def cleanup(self) -> None:
        """
        Clean up agent resources.

        Releases any resources held by the agent. Should be called
        when the agent is no longer needed.
        """
        try:
            logger.info(f"Cleaning up agent '{self.agent_name}'")
            self._cleanup_resources()
            self.state = AgentState.IDLE
            self._initialized = False
            logger.info(f"Agent '{self.agent_name}' cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up agent '{self.agent_name}': {e}")

    def _send_message(
        self,
        execution_context: ExecutionContext,
        message_type: MessageType,
        payload: Dict[str, Any],
        recipient: Optional[str] = None,
    ) -> None:
        """Send a message through the execution context."""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender=self.agent_name,
            recipient=recipient,
            payload=payload,
        )
        execution_context.add_message(message)

    def _initialize_resources(self) -> None:
        """
        Initialize agent-specific resources.

        Override this method to set up resources like database connections,
        API clients, models, etc.
        """
        pass

    def _cleanup_resources(self) -> None:
        """
        Clean up agent-specific resources.

        Override this method to release resources like closing connections,
        releasing memory, etc.
        """
        pass

    @abstractmethod
    def _validate_input(self, input_data: TInput) -> TInput:
        """
        Validate and potentially transform input data.

        Args:
            input_data: Raw input data

        Returns:
            Validated input data

        Raises:
            AgentValidationError: If validation fails
        """
        pass

    @abstractmethod
    def _process(self, input_data: TInput, context: AgentContext) -> TOutput:
        """
        Process the input and produce output.

        This is the main agent logic that must be implemented by
        concrete agent classes.

        Args:
            input_data: Validated input data
            context: Agent execution context

        Returns:
            Output data

        Raises:
            AgentExecutionError: If processing fails
        """
        pass

    def _validate_output(self, output: TOutput) -> TOutput:
        """
        Validate output data.

        Override this method to add custom output validation.
        Default implementation just returns the output.

        Args:
            output: Raw output data

        Returns:
            Validated output data

        Raises:
            AgentValidationError: If validation fails
        """
        return output
