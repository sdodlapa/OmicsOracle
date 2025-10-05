"""
Request Tracing and Debugging System

Provides comprehensive end-to-end visibility into query execution,
from frontend input to final response rendering.

Features:
- Unique trace IDs for every request
- Structured event logging
- Performance metrics at each stage
- Error tracking and stack traces
- External API call monitoring
- Database query logging
"""

import json
import logging
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events in the system."""
    
    # Request lifecycle
    REQUEST_STARTED = "request_started"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_FAILED = "request_failed"
    
    # Workflow stages
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_STAGE_STARTED = "workflow_stage_started"
    WORKFLOW_STAGE_COMPLETED = "workflow_stage_completed"
    WORKFLOW_STAGE_FAILED = "workflow_stage_failed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    
    # Agent execution
    AGENT_STARTED = "agent_started"
    AGENT_PROCESSING = "agent_processing"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    
    # External APIs
    EXTERNAL_API_CALL = "external_api_call"
    EXTERNAL_API_RESPONSE = "external_api_response"
    EXTERNAL_API_ERROR = "external_api_error"
    
    # Database
    DATABASE_QUERY = "database_query"
    DATABASE_RESPONSE = "database_response"
    DATABASE_ERROR = "database_error"
    
    # Cache
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_SET = "cache_set"
    
    # Frontend
    FRONTEND_QUERY_ENTERED = "frontend_query_entered"
    FRONTEND_RESULTS_RENDERED = "frontend_results_rendered"


class TraceEvent(BaseModel):
    """A single event in a request trace."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str = Field(..., description="Request trace ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType = Field(..., description="Type of event")
    
    # Context
    component: str = Field(..., description="Component generating event (e.g., 'QueryAgent', 'SearchAgent')")
    action: str = Field(..., description="Action being performed")
    
    # Data
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input to this stage")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output from this stage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Performance
    duration_ms: Optional[float] = Field(None, description="Duration in milliseconds")
    
    # Error tracking
    error: Optional[str] = Field(None, description="Error message if failed")
    stack_trace: Optional[str] = Field(None, description="Stack trace if error occurred")
    
    # Relationships
    parent_event_id: Optional[str] = Field(None, description="Parent event ID for nested events")


class RequestTrace(BaseModel):
    """Complete trace of a single request through the system."""
    
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Request details
    user_id: Optional[str] = None
    query: str = Field(..., description="User's original query")
    workflow_type: str = Field(..., description="Type of workflow executed")
    
    # Events
    events: List[TraceEvent] = Field(default_factory=list)
    
    # Summary metrics
    total_duration_ms: Optional[float] = None
    total_events: int = 0
    success: bool = False
    error_message: Optional[str] = None
    
    # Results summary
    datasets_found: int = 0
    datasets_analyzed: int = 0
    report_generated: bool = False


class TraceContext:
    """Context manager for tracing execution."""
    
    def __init__(self, trace_id: str, component: str, action: str, metadata: Optional[Dict] = None):
        self.trace_id = trace_id
        self.component = component
        self.action = action
        self.metadata = metadata or {}
        self.start_time = None
        self.event_id = str(uuid4())
        
    def __enter__(self):
        self.start_time = time.time()
        
        # Log start event
        event = TraceEvent(
            event_id=self.event_id,
            trace_id=self.trace_id,
            event_type=self._get_start_event_type(),
            component=self.component,
            action=self.action,
            metadata=self.metadata
        )
        
        RequestTracer.add_event(self.trace_id, event)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type is None:
            # Success
            event = TraceEvent(
                trace_id=self.trace_id,
                event_type=self._get_complete_event_type(),
                component=self.component,
                action=self.action,
                duration_ms=duration_ms,
                parent_event_id=self.event_id
            )
        else:
            # Failure
            event = TraceEvent(
                trace_id=self.trace_id,
                event_type=self._get_failure_event_type(),
                component=self.component,
                action=self.action,
                duration_ms=duration_ms,
                error=str(exc_val),
                stack_trace=traceback.format_exc(),
                parent_event_id=self.event_id
            )
        
        RequestTracer.add_event(self.trace_id, event)
        
    def _get_start_event_type(self) -> EventType:
        """Determine start event type based on component."""
        if "Agent" in self.component:
            return EventType.AGENT_STARTED
        elif self.component == "Workflow":
            return EventType.WORKFLOW_STAGE_STARTED
        else:
            return EventType.REQUEST_STARTED
    
    def _get_complete_event_type(self) -> EventType:
        """Determine completion event type based on component."""
        if "Agent" in self.component:
            return EventType.AGENT_COMPLETED
        elif self.component == "Workflow":
            return EventType.WORKFLOW_STAGE_COMPLETED
        else:
            return EventType.REQUEST_COMPLETED
    
    def _get_failure_event_type(self) -> EventType:
        """Determine failure event type based on component."""
        if "Agent" in self.component:
            return EventType.AGENT_FAILED
        elif self.component == "Workflow":
            return EventType.WORKFLOW_STAGE_FAILED
        else:
            return EventType.REQUEST_FAILED


class RequestTracer:
    """
    Global request tracer for tracking all requests.
    
    Usage:
        # Start a new trace
        trace_id = RequestTracer.start_trace(query="Find cancer datasets", workflow_type="full_analysis")
        
        # Add events
        with TraceContext(trace_id, "QueryAgent", "process_query"):
            # Do work
            pass
        
        # Complete trace
        trace = RequestTracer.complete_trace(trace_id, success=True)
        
        # Get trace for debugging
        trace = RequestTracer.get_trace(trace_id)
    """
    
    _traces: Dict[str, RequestTrace] = {}
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def start_trace(cls, query: str, workflow_type: str, user_id: Optional[str] = None) -> str:
        """Start a new request trace."""
        trace = RequestTrace(
            query=query,
            workflow_type=workflow_type,
            user_id=user_id
        )
        
        cls._traces[trace.trace_id] = trace
        
        cls._logger.info(
            f"[TRACE] Started trace {trace.trace_id} - Query: '{query}' - Workflow: {workflow_type}",
            extra={"trace_id": trace.trace_id, "query": query, "workflow_type": workflow_type}
        )
        
        return trace.trace_id
    
    @classmethod
    def add_event(cls, trace_id: str, event: TraceEvent):
        """Add an event to a trace."""
        if trace_id not in cls._traces:
            cls._logger.warning(f"Trace {trace_id} not found, creating new trace")
            cls._traces[trace_id] = RequestTrace(
                trace_id=trace_id,
                query="Unknown",
                workflow_type="Unknown"
            )
        
        trace = cls._traces[trace_id]
        trace.events.append(event)
        trace.total_events += 1
        
        # Log event
        cls._logger.info(
            f"[TRACE] {trace_id} - {event.event_type.value} - {event.component}: {event.action}",
            extra={
                "trace_id": trace_id,
                "event_type": event.event_type.value,
                "component": event.component,
                "action": event.action,
                "duration_ms": event.duration_ms
            }
        )
    
    @classmethod
    def complete_trace(
        cls,
        trace_id: str,
        success: bool,
        error_message: Optional[str] = None,
        datasets_found: int = 0,
        datasets_analyzed: int = 0,
        report_generated: bool = False
    ) -> RequestTrace:
        """Complete a trace and calculate summary metrics."""
        if trace_id not in cls._traces:
            cls._logger.error(f"Trace {trace_id} not found")
            raise ValueError(f"Trace {trace_id} not found")
        
        trace = cls._traces[trace_id]
        trace.completed_at = datetime.now(timezone.utc)
        trace.success = success
        trace.error_message = error_message
        trace.datasets_found = datasets_found
        trace.datasets_analyzed = datasets_analyzed
        trace.report_generated = report_generated
        
        # Calculate total duration
        if trace.started_at and trace.completed_at:
            trace.total_duration_ms = (
                trace.completed_at - trace.started_at
            ).total_seconds() * 1000
        
        cls._logger.info(
            f"[TRACE] Completed trace {trace_id} - Success: {success} - "
            f"Duration: {trace.total_duration_ms:.2f}ms - Events: {trace.total_events}",
            extra={
                "trace_id": trace_id,
                "success": success,
                "duration_ms": trace.total_duration_ms,
                "total_events": trace.total_events,
                "datasets_found": datasets_found
            }
        )
        
        return trace
    
    @classmethod
    def get_trace(cls, trace_id: str) -> Optional[RequestTrace]:
        """Get a trace by ID."""
        return cls._traces.get(trace_id)
    
    @classmethod
    def get_all_traces(cls) -> List[RequestTrace]:
        """Get all traces."""
        return list(cls._traces.values())
    
    @classmethod
    def clear_old_traces(cls, max_age_hours: int = 24):
        """Clear traces older than max_age_hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        to_delete = [
            trace_id
            for trace_id, trace in cls._traces.items()
            if trace.started_at.timestamp() < cutoff
        ]
        
        for trace_id in to_delete:
            del cls._traces[trace_id]
        
        cls._logger.info(f"Cleared {len(to_delete)} old traces")
    
    @classmethod
    def export_trace(cls, trace_id: str, format: str = "json") -> str:
        """Export a trace for debugging."""
        trace = cls.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace {trace_id} not found")
        
        if format == "json":
            return trace.model_dump_json(indent=2)
        elif format == "timeline":
            return cls._format_timeline(trace)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    @classmethod
    def _format_timeline(cls, trace: RequestTrace) -> str:
        """Format trace as a timeline."""
        lines = [
            f"=" * 80,
            f"TRACE TIMELINE: {trace.trace_id}",
            f"Query: {trace.query}",
            f"Workflow: {trace.workflow_type}",
            f"Started: {trace.started_at.isoformat()}",
            f"Duration: {trace.total_duration_ms:.2f}ms" if trace.total_duration_ms else "In Progress",
            f"Success: {trace.success}",
            f"=" * 80,
            ""
        ]
        
        for i, event in enumerate(trace.events, 1):
            status = "✅" if "completed" in event.event_type.value else "❌" if "failed" in event.event_type.value else "🔄"
            duration = f"({event.duration_ms:.2f}ms)" if event.duration_ms else ""
            
            lines.append(
                f"{i:3d}. {status} [{event.timestamp.strftime('%H:%M:%S.%f')[:-3]}] "
                f"{event.component}: {event.action} {duration}"
            )
            
            if event.error:
                lines.append(f"     ERROR: {event.error}")
        
        lines.append("")
        lines.append(f"=" * 80)
        lines.append(f"Total Events: {trace.total_events}")
        lines.append(f"Datasets Found: {trace.datasets_found}")
        lines.append(f"Datasets Analyzed: {trace.datasets_analyzed}")
        lines.append(f"Report Generated: {trace.report_generated}")
        lines.append(f"=" * 80)
        
        return "\n".join(lines)


# Convenience functions

def trace_function(component: str, action: Optional[str] = None):
    """Decorator for tracing function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get trace_id from kwargs or args
            trace_id = kwargs.get('trace_id') or getattr(args[0], 'trace_id', None) if args else None
            
            if not trace_id:
                # No tracing available
                return func(*args, **kwargs)
            
            action_name = action or func.__name__
            
            with TraceContext(trace_id, component, action_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


@contextmanager
def trace_external_api(trace_id: str, service: str, endpoint: str, method: str = "GET"):
    """Context manager for tracing external API calls."""
    start_time = time.time()
    
    event = TraceEvent(
        trace_id=trace_id,
        event_type=EventType.EXTERNAL_API_CALL,
        component=service,
        action=f"{method} {endpoint}",
        metadata={"method": method, "endpoint": endpoint}
    )
    RequestTracer.add_event(trace_id, event)
    
    try:
        yield
        
        duration_ms = (time.time() - start_time) * 1000
        event = TraceEvent(
            trace_id=trace_id,
            event_type=EventType.EXTERNAL_API_RESPONSE,
            component=service,
            action=f"{method} {endpoint}",
            duration_ms=duration_ms
        )
        RequestTracer.add_event(trace_id, event)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        event = TraceEvent(
            trace_id=trace_id,
            event_type=EventType.EXTERNAL_API_ERROR,
            component=service,
            action=f"{method} {endpoint}",
            duration_ms=duration_ms,
            error=str(e),
            stack_trace=traceback.format_exc()
        )
        RequestTracer.add_event(trace_id, event)
        raise
