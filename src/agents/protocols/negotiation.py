"""
Negotiation Protocol - Enables agents to request information from each other.
Implements structured request/response patterns for agent collaboration.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..base import BaseAgent

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Priority levels for information requests."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class RequestStatus(Enum):
    """Status of an information request."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    TIMEOUT = "timeout"


@dataclass
class InfoRequest:
    """
    A request for information from one agent to another.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    query: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.NORMAL
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "query": self.query,
            "context": self.context,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class InfoResponse:
    """
    A response to an information request.
    """
    request_id: str
    from_agent: str
    content: str
    confidence: float  # 0-1, how confident the agent is in this response
    can_help: bool  # Whether the agent was able to help
    status: RequestStatus = RequestStatus.COMPLETED
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "from_agent": self.from_agent,
            "content": self.content,
            "confidence": self.confidence,
            "can_help": self.can_help,
            "status": self.status.value,
            "metadata": self.metadata
        }


class NegotiationProtocol:
    """
    Protocol for agent-to-agent information exchange.
    
    Enables agents to:
    1. Check if another agent can help with a query
    2. Request specific information from peers
    3. Receive and process responses
    4. Chain multiple agents for complex queries
    """
    
    def __init__(self, agents: Dict[str, 'BaseAgent']):
        """
        Initialize the negotiation protocol.
        
        Args:
            agents: Dictionary mapping agent names to agent instances
        """
        self.agents = agents
        self.pending_requests: Dict[str, InfoRequest] = {}
        self.responses: Dict[str, InfoResponse] = {}
        
        logger.info(f"NegotiationProtocol initialized with {len(agents)} agents")
    
    def can_help_with(self, agent_name: str, query: str) -> tuple[bool, float]:
        """
        Check if an agent can help with a query.
        
        Args:
            agent_name: Name of the agent to check
            query: The query to check
            
        Returns:
            Tuple of (can_help, confidence)
        """
        if agent_name not in self.agents:
            return False, 0.0
        
        agent = self.agents[agent_name]
        
        # Check if agent has a custom implementation
        if hasattr(agent, 'can_help_with'):
            return agent.can_help_with(query)
        
        # Default: use system prompt similarity (basic heuristic)
        system_prompt = agent.get_system_prompt().lower()
        query_lower = query.lower()
        
        # Simple keyword overlap check
        query_words = set(query_lower.split())
        prompt_words = set(system_prompt.split())
        overlap = len(query_words & prompt_words) / max(len(query_words), 1)
        
        return overlap > 0.1, min(1.0, overlap * 2)
    
    def request_info(
        self,
        from_agent: str,
        to_agent: str,
        query: str,
        context: Optional[Dict] = None,
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> InfoResponse:
        """
        Send an information request from one agent to another.
        
        This is a synchronous operation that waits for a response.
        
        Args:
            from_agent: Name of the requesting agent
            to_agent: Name of the target agent
            query: The query/question
            context: Additional context to help the target agent
            priority: Priority level of the request
            
        Returns:
            InfoResponse from the target agent
        """
        if to_agent not in self.agents:
            return InfoResponse(
                request_id="",
                from_agent=to_agent,
                content=f"Agent '{to_agent}' not found",
                confidence=0.0,
                can_help=False,
                status=RequestStatus.REJECTED
            )
        
        # Create request
        request = InfoRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            query=query,
            context=context or {},
            priority=priority
        )
        
        self.pending_requests[request.id] = request
        logger.info(f"[Negotiation] {from_agent} -> {to_agent}: {query[:50]}...")
        
        try:
            # Get target agent
            target_agent = self.agents[to_agent]
            
            # Check if agent can help first
            can_help, confidence = self.can_help_with(to_agent, query)
            
            if not can_help:
                response = InfoResponse(
                    request_id=request.id,
                    from_agent=to_agent,
                    content="I don't have expertise in this area.",
                    confidence=0.0,
                    can_help=False,
                    status=RequestStatus.REJECTED
                )
            else:
                # Execute query on target agent
                # Build context-enhanced query
                enhanced_query = query
                if context:
                    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                    enhanced_query = f"Context from {from_agent}:\n{context_str}\n\nQuery: {query}"
                
                # Run the agent
                result = target_agent.run(enhanced_query)
                
                response = InfoResponse(
                    request_id=request.id,
                    from_agent=to_agent,
                    content=result,
                    confidence=confidence,
                    can_help=True,
                    status=RequestStatus.COMPLETED
                )
            
            # Store response
            self.responses[request.id] = response
            del self.pending_requests[request.id]
            
            logger.info(f"[Negotiation] Response from {to_agent}: {response.can_help}, confidence={response.confidence:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"[Negotiation] Error processing request: {e}")
            response = InfoResponse(
                request_id=request.id,
                from_agent=to_agent,
                content=f"Error: {str(e)}",
                confidence=0.0,
                can_help=False,
                status=RequestStatus.REJECTED
            )
            self.responses[request.id] = response
            return response
    
    def find_helpers(self, query: str, min_confidence: float = 0.3) -> List[tuple[str, float]]:
        """
        Find all agents that can help with a query.
        
        Args:
            query: The query to find helpers for
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of (agent_name, confidence) tuples, sorted by confidence
        """
        helpers = []
        
        for agent_name in self.agents:
            can_help, confidence = self.can_help_with(agent_name, query)
            if can_help and confidence >= min_confidence:
                helpers.append((agent_name, confidence))
        
        # Sort by confidence descending
        helpers.sort(key=lambda x: x[1], reverse=True)
        return helpers
    
    def collaborative_query(
        self,
        initiator: str,
        query: str,
        max_agents: int = 3
    ) -> Dict[str, InfoResponse]:
        """
        Execute a query across multiple collaborating agents.
        
        The initiator agent asks relevant peers for information,
        then all responses are returned.
        
        Args:
            initiator: The agent initiating the collaboration
            query: The query to execute
            max_agents: Maximum number of agents to consult
            
        Returns:
            Dictionary mapping agent names to their responses
        """
        # Find agents that can help
        helpers = self.find_helpers(query)
        
        # Exclude initiator
        helpers = [(name, conf) for name, conf in helpers if name != initiator]
        
        # Limit to max_agents
        helpers = helpers[:max_agents]
        
        responses = {}
        for agent_name, _ in helpers:
            response = self.request_info(
                from_agent=initiator,
                to_agent=agent_name,
                query=query,
                context={"collaboration_mode": True, "initiator": initiator}
            )
            responses[agent_name] = response
        
        return responses
    
    def get_pending_requests(self, agent_name: str) -> List[InfoRequest]:
        """Get all pending requests for an agent."""
        return [
            req for req in self.pending_requests.values()
            if req.to_agent == agent_name
        ]
