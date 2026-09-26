"""Tracer for capturing agent decisions and tool calls."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Types of trace events."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DECISION = "decision"
    ERROR = "error"
    RETRY = "retry"
    MEMORY_OP = "memory_op"
    DEBATE_ROUND = "debate_round"
    THOUGHT_TREE_NODE = "thought_tree_node"


@dataclass
class TraceEvent:
    """Single trace event."""
    event_type: EventType
    timestamp: datetime
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["event_type"] = self.event_type.value
        return result


class Tracer:
    """Tracer for capturing system execution traces."""
    
    def __init__(self):
        """Initialize tracer."""
        self.events: List[TraceEvent] = []
        self.enabled = True
    
    def trace(
        self,
        event_type: EventType,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a trace event."""
        if not self.enabled:
            return
        
        event = TraceEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            agent_name=agent_name,
            tool_name=tool_name,
            input=input,
            output=output,
            error=error,
            metadata=metadata or {}
        )
        self.events.append(event)
    
    def agent_start(self, agent_name: str, input: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Trace agent start."""
        self.trace(EventType.AGENT_START, agent_name=agent_name, input=input, metadata=metadata)
    
    def agent_end(self, agent_name: str, output: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Trace agent end."""
        self.trace(EventType.AGENT_END, agent_name=agent_name, output=output, metadata=metadata)
    
    def tool_call(self, agent_name: str, tool_name: str, input: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Trace tool call."""
        self.trace(EventType.TOOL_CALL, agent_name=agent_name, tool_name=tool_name, input=input, metadata=metadata)
    
    def tool_result(self, agent_name: str, tool_name: str, output: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Trace tool result."""
        self.trace(EventType.TOOL_RESULT, agent_name=agent_name, tool_name=tool_name, output=output, metadata=metadata)
    
    def decision(self, agent_name: str, decision: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Trace agent decision."""
        self.trace(EventType.DECISION, agent_name=agent_name, input=decision, metadata=metadata)
    
    def error(self, agent_name: Optional[str], error: str, metadata: Optional[Dict[str, Any]] = None):
        """Trace error."""
        self.trace(EventType.ERROR, agent_name=agent_name, error=error, metadata=metadata)
    
    def retry(self, agent_name: str, attempt: int, metadata: Optional[Dict[str, Any]] = None):
        """Trace retry."""
        self.trace(EventType.RETRY, agent_name=agent_name, metadata={"attempt": attempt, **(metadata or {})})
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """Get all trace events as list of dicts."""
        return [event.to_dict() for event in self.events]
    
    def clear(self):
        """Clear all traces."""
        self.events.clear()
