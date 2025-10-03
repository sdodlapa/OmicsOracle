"""Tests for agent base framework."""

import pytest
from pydantic import BaseModel

from omics_oracle_v2.agents.base import Agent, AgentResult, AgentState
from omics_oracle_v2.agents.context import AgentContext, ExecutionContext, MessageType
from omics_oracle_v2.agents.exceptions import AgentStateError, AgentValidationError
from omics_oracle_v2.core.config import Settings


# Test input/output models
class TestInput(BaseModel):
    """Test input model."""

    value: str
    count: int = 1


class TestOutput(BaseModel):
    """Test output model."""

    result: str
    processed_count: int


# Concrete agent implementation for testing
class SuccessfulAgent(Agent[TestInput, TestOutput]):
    """Agent that always succeeds."""

    def _validate_input(self, input_data: TestInput) -> TestInput:
        if input_data.count < 0:
            raise AgentValidationError("Count must be non-negative")
        return input_data

    def _process(self, input_data: TestInput, context: AgentContext) -> TestOutput:
        result = input_data.value.upper()
        processed_count = input_data.count * 2
        context.set_metric("processed_value", result)
        return TestOutput(result=result, processed_count=processed_count)


class FailingAgent(Agent[TestInput, TestOutput]):
    """Agent that always fails during processing."""

    def _validate_input(self, input_data: TestInput) -> TestInput:
        return input_data

    def _process(self, input_data: TestInput, context: AgentContext) -> TestOutput:
        raise RuntimeError("Simulated processing failure")


class ValidationErrorAgent(Agent[TestInput, TestOutput]):
    """Agent that fails during input validation."""

    def _validate_input(self, input_data: TestInput) -> TestInput:
        raise AgentValidationError("Invalid input")

    def _process(self, input_data: TestInput, context: AgentContext) -> TestOutput:
        return TestOutput(result="", processed_count=0)


class TestAgentState:
    """Test AgentState enum."""

    def test_agent_states(self):
        """Test all agent states are defined."""
        assert AgentState.IDLE == "idle"
        assert AgentState.INITIALIZING == "initializing"
        assert AgentState.READY == "ready"
        assert AgentState.RUNNING == "running"
        assert AgentState.COMPLETED == "completed"
        assert AgentState.FAILED == "failed"
        assert AgentState.TIMEOUT == "timeout"


class TestAgentResult:
    """Test AgentResult model."""

    def test_successful_result(self):
        """Test creating a successful result."""
        output = TestOutput(result="SUCCESS", processed_count=10)
        result = AgentResult(
            agent_name="TestAgent",
            state=AgentState.COMPLETED,
            output=output,
            execution_time_ms=123.45,
        )

        assert result.agent_name == "TestAgent"
        assert result.state == AgentState.COMPLETED
        assert result.output == output
        assert result.error is None
        assert result.execution_time_ms == 123.45
        assert result.success is True

    def test_failed_result(self):
        """Test creating a failed result."""
        result = AgentResult(
            agent_name="TestAgent",
            state=AgentState.FAILED,
            output=None,
            error="Something went wrong",
            execution_time_ms=50.0,
        )

        assert result.state == AgentState.FAILED
        assert result.output is None
        assert result.error == "Something went wrong"
        assert result.success is False

    def test_result_with_metadata(self):
        """Test result with metadata."""
        output = TestOutput(result="OK", processed_count=5)
        result = AgentResult(
            agent_name="TestAgent",
            state=AgentState.COMPLETED,
            output=output,
            execution_time_ms=100.0,
            metadata={"custom_metric": 42, "iterations": 3},
        )

        assert result.metadata["custom_metric"] == 42
        assert result.metadata["iterations"] == 3


class TestAgentLifecycle:
    """Test agent lifecycle management."""

    def test_agent_creation(self):
        """Test creating an agent."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        assert agent.agent_name == "SuccessfulAgent"
        assert agent.state == AgentState.IDLE
        assert agent.context is None
        assert agent._initialized is False

    def test_agent_custom_name(self):
        """Test creating an agent with custom name."""
        settings = Settings()
        agent = SuccessfulAgent(settings, agent_name="MyCustomAgent")

        assert agent.agent_name == "MyCustomAgent"

    def test_agent_initialization(self):
        """Test agent initialization."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        agent.initialize()

        assert agent.state == AgentState.READY
        assert agent._initialized is True

    def test_double_initialization_error(self):
        """Test that initializing twice raises error."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        agent.initialize()

        with pytest.raises(AgentStateError, match="already initialized"):
            agent.initialize()

    def test_agent_cleanup(self):
        """Test agent cleanup."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        agent.initialize()
        assert agent.state == AgentState.READY

        agent.cleanup()

        assert agent.state == AgentState.IDLE
        assert agent._initialized is False


class TestAgentExecution:
    """Test agent execution."""

    def test_successful_execution(self):
        """Test successful agent execution."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        input_data = TestInput(value="hello", count=5)
        result = agent.execute(input_data)

        assert result.success is True
        assert result.state == AgentState.COMPLETED
        assert result.output is not None
        assert result.output.result == "HELLO"
        assert result.output.processed_count == 10
        assert result.execution_time_ms > 0
        assert result.error is None

    def test_auto_initialization(self):
        """Test that execute auto-initializes agent."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        assert agent._initialized is False

        input_data = TestInput(value="test", count=1)
        result = agent.execute(input_data)

        assert agent._initialized is True
        assert result.success is True

    def test_execution_with_validation_error(self):
        """Test execution with input validation error."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        input_data = TestInput(value="test", count=-1)  # Invalid count
        result = agent.execute(input_data)

        assert result.success is False
        assert result.state == AgentState.FAILED
        assert result.output is None
        assert "Count must be non-negative" in result.error
        assert result.execution_time_ms > 0

    def test_execution_with_processing_error(self):
        """Test execution with processing error."""
        settings = Settings()
        agent = FailingAgent(settings)

        input_data = TestInput(value="test", count=1)
        result = agent.execute(input_data)

        assert result.success is False
        assert result.state == AgentState.FAILED
        assert result.output is None
        assert "Simulated processing failure" in result.error

    def test_execution_not_ready_after_failure(self):
        """Test that agent can't execute after failure without re-init."""
        settings = Settings()
        agent = ValidationErrorAgent(settings)

        input_data = TestInput(value="test", count=1)
        result1 = agent.execute(input_data)
        assert result1.success is False
        assert result1.state == AgentState.FAILED

        # Second execution should fail due to state
        with pytest.raises(AgentStateError, match="is not ready"):
            agent.execute(input_data)

    def test_execution_with_context(self):
        """Test execution creates agent context."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        input_data = TestInput(value="test", count=3)
        _result = agent.execute(input_data)  # noqa: F841

        assert agent.context is not None
        assert agent.context.agent_name == "SuccessfulAgent"
        assert agent.context.end_time is not None
        assert "processed_value" in agent.context.metrics
        assert agent.context.metrics["processed_value"] == "TEST"

    def test_execution_with_execution_context(self):
        """Test execution with workflow execution context."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        execution_context = ExecutionContext(execution_id="test-123", workflow_name="test-workflow")

        input_data = TestInput(value="hello", count=2)
        result = agent.execute(input_data, execution_context=execution_context)

        assert result.success is True
        assert "SuccessfulAgent" in execution_context.agent_contexts
        assert len(execution_context.messages) > 0

        # Check messages
        messages = execution_context.messages
        message_types = [m.message_type for m in messages]
        assert MessageType.STATUS in message_types
        assert MessageType.RESULT in message_types

    def test_multiple_executions(self):
        """Test multiple executions with same agent."""
        settings = Settings()
        agent = SuccessfulAgent(settings)

        # First execution
        result1 = agent.execute(TestInput(value="first", count=1))
        assert result1.success is True
        assert result1.output.result == "FIRST"

        # Second execution
        result2 = agent.execute(TestInput(value="second", count=2))
        assert result2.success is True
        assert result2.output.result == "SECOND"
        assert result2.output.processed_count == 4


class TestAgentContext:
    """Test agent context functionality."""

    def test_context_creation(self):
        """Test creating agent context."""
        context = AgentContext(agent_name="TestAgent")

        assert context.agent_name == "TestAgent"
        assert context.start_time is not None
        assert context.end_time is None
        assert len(context.messages) == 0
        assert len(context.errors) == 0
        assert len(context.metrics) == 0

    def test_context_add_error(self):
        """Test adding errors to context."""
        context = AgentContext(agent_name="TestAgent")

        context.add_error("Error 1")
        context.add_error("Error 2")

        assert len(context.errors) == 2
        assert "Error 1" in context.errors
        assert "Error 2" in context.errors

    def test_context_set_metric(self):
        """Test setting metrics in context."""
        context = AgentContext(agent_name="TestAgent")

        context.set_metric("execution_time", 123.45)
        context.set_metric("item_count", 42)

        assert context.metrics["execution_time"] == 123.45
        assert context.metrics["item_count"] == 42

    def test_context_duration(self):
        """Test calculating context duration."""
        import time
        from datetime import datetime

        context = AgentContext(agent_name="TestAgent")

        # Initially no duration
        assert context.get_duration_ms() is None

        # Set end time
        time.sleep(0.01)  # Small delay
        context.end_time = datetime.utcnow()

        duration = context.get_duration_ms()
        assert duration is not None
        assert duration >= 10  # At least 10ms


class TestExecutionContext:
    """Test execution context functionality."""

    def test_execution_context_creation(self):
        """Test creating execution context."""
        context = ExecutionContext(execution_id="exec-123", workflow_name="test-workflow")

        assert context.execution_id == "exec-123"
        assert context.workflow_name == "test-workflow"
        assert context.start_time is not None
        assert context.end_time is None
        assert len(context.agent_contexts) == 0
        assert len(context.messages) == 0
        assert context.success is True
        assert context.error is None

    def test_get_or_create_agent_context(self):
        """Test getting or creating agent context."""
        context = ExecutionContext(execution_id="exec-123", workflow_name="test-workflow")

        # Create new context
        agent_ctx1 = context.get_or_create_agent_context("Agent1")
        assert agent_ctx1.agent_name == "Agent1"
        assert "Agent1" in context.agent_contexts

        # Get existing context
        agent_ctx2 = context.get_or_create_agent_context("Agent1")
        assert agent_ctx2 is agent_ctx1  # Same object

    def test_global_state(self):
        """Test global state management."""
        context = ExecutionContext(execution_id="exec-123", workflow_name="test-workflow")

        context.set_global_state("query", "test query")
        context.set_global_state("max_results", 100)

        assert context.get_global_state("query") == "test query"
        assert context.get_global_state("max_results") == 100
        assert context.get_global_state("nonexistent") is None
        assert context.get_global_state("nonexistent", "default") == "default"

    def test_finish_workflow(self):
        """Test finishing workflow execution."""
        import time

        context = ExecutionContext(execution_id="exec-123", workflow_name="test-workflow")

        # Create some agent contexts
        context.get_or_create_agent_context("Agent1")
        context.get_or_create_agent_context("Agent2")

        time.sleep(0.01)
        context.finish(success=True)

        assert context.end_time is not None
        assert context.success is True
        assert context.error is None
        assert context.get_duration_ms() >= 10

        # Check all agent contexts are finished
        for agent_ctx in context.agent_contexts.values():
            assert agent_ctx.end_time is not None

    def test_finish_workflow_with_error(self):
        """Test finishing workflow with error."""
        context = ExecutionContext(execution_id="exec-123", workflow_name="test-workflow")

        context.finish(success=False, error="Workflow failed")

        assert context.end_time is not None
        assert context.success is False
        assert context.error == "Workflow failed"
