"""
Message Bus - Central hub for inter-agent communication.
Enables publish/subscribe patterns and knowledge broadcasting.
"""
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

if TYPE_CHECKING:
    from ...memory.shared_pool import SharedMemoryPool

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages on the bus."""
    INFO_REQUEST = "info_request"
    INFO_RESPONSE = "info_response"
    KNOWLEDGE_SHARE = "knowledge_share"
    ALERT = "alert"
    STATUS_UPDATE = "status_update"


@dataclass
class AgentMessage:
    """A message on the inter-agent bus."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.KNOWLEDGE_SHARE
    source_agent: str = ""
    target_agents: List[str] = field(default_factory=list)  # Empty = broadcast to all
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "message_type": self.message_type.value,
            "source_agent": self.source_agent,
            "target_agents": self.target_agents,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class MessageBus:
    """
    Central message bus for inter-agent communication.
    
    Features:
    1. Publish/Subscribe pattern for agents
    2. Topic-based message filtering
    3. Integration with shared memory for persistence
    4. Message history tracking
    """
    
    def __init__(
        self,
        shared_memory: Optional['SharedMemoryPool'] = None,
        persist_messages: bool = True,
        max_history: int = 100
    ):
        """
        Initialize the message bus.
        
        Args:
            shared_memory: Optional shared memory pool for persistence
            persist_messages: Whether to persist important messages
            max_history: Maximum messages to keep in history
        """
        self.shared_memory = shared_memory
        self.persist_messages = persist_messages and shared_memory is not None
        self.max_history = max_history
        
        # Subscriptions: agent_name -> list of callbacks
        self._subscriptions: Dict[str, List[Callable[[AgentMessage], None]]] = defaultdict(list)
        
        # Topic subscriptions: topic -> list of (agent_name, callback)
        self._topic_subscriptions: Dict[str, List[tuple[str, Callable]]] = defaultdict(list)
        
        # Message history
        self._history: List[AgentMessage] = []
        
        # Pending messages for offline agents
        self._pending: Dict[str, List[AgentMessage]] = defaultdict(list)
        
        logger.info("MessageBus initialized")
    
    def subscribe(
        self,
        agent_name: str,
        callback: Callable[[AgentMessage], None],
        topics: Optional[List[str]] = None
    ):
        """
        Subscribe an agent to receive messages.
        
        Args:
            agent_name: Name of the subscribing agent
            callback: Function to call when a message is received
            topics: Optional list of topics to subscribe to
        """
        self._subscriptions[agent_name].append(callback)
        
        if topics:
            for topic in topics:
                self._topic_subscriptions[topic].append((agent_name, callback))
        
        # Deliver any pending messages
        if agent_name in self._pending:
            for msg in self._pending[agent_name]:
                try:
                    callback(msg)
                except Exception as e:
                    logger.error(f"Error delivering pending message to {agent_name}: {e}")
            del self._pending[agent_name]
        
        logger.info(f"Agent '{agent_name}' subscribed to message bus")
    
    def unsubscribe(self, agent_name: str):
        """Unsubscribe an agent from the bus."""
        if agent_name in self._subscriptions:
            del self._subscriptions[agent_name]
        
        # Remove from topic subscriptions
        for topic in self._topic_subscriptions:
            self._topic_subscriptions[topic] = [
                (name, cb) for name, cb in self._topic_subscriptions[topic]
                if name != agent_name
            ]
        
        logger.info(f"Agent '{agent_name}' unsubscribed from message bus")
    
    def publish(self, message: AgentMessage) -> str:
        """
        Publish a message to the bus.
        
        Args:
            message: The message to publish
            
        Returns:
            Message ID
        """
        # Add to history
        self._history.append(message)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
        
        # Persist important messages to shared memory
        if self.persist_messages and message.message_type in [
            MessageType.KNOWLEDGE_SHARE,
            MessageType.ALERT
        ]:
            self._persist_message(message)
        
        # Deliver to target agents
        if message.target_agents:
            # Targeted message
            for target in message.target_agents:
                self._deliver_to_agent(target, message)
        else:
            # Broadcast to all (except source)
            for agent_name in self._subscriptions:
                if agent_name != message.source_agent:
                    self._deliver_to_agent(agent_name, message)
        
        logger.info(f"Published message {message.id} from {message.source_agent}")
        return message.id
    
    def _deliver_to_agent(self, agent_name: str, message: AgentMessage):
        """Deliver a message to a specific agent."""
        if agent_name in self._subscriptions:
            for callback in self._subscriptions[agent_name]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error delivering message to {agent_name}: {e}")
        else:
            # Agent not subscribed - queue for later
            self._pending[agent_name].append(message)
    
    def _persist_message(self, message: AgentMessage):
        """Persist message to shared memory."""
        if not self.shared_memory:
            return
        
        try:
            visibility = message.target_agents if message.target_agents else "global"
            self.shared_memory.add(
                content=f"[{message.message_type.value}] {message.content}",
                source_agent=message.source_agent,
                visibility=visibility,
                importance=0.7 if message.message_type == MessageType.ALERT else 0.5,
                metadata=message.metadata
            )
        except Exception as e:
            logger.error(f"Failed to persist message: {e}")
    
    def broadcast(
        self,
        content: str,
        source_agent: str,
        message_type: MessageType = MessageType.KNOWLEDGE_SHARE,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Broadcast a message to all agents.
        
        Args:
            content: Message content
            source_agent: Agent sending the message
            message_type: Type of message
            metadata: Optional metadata
            
        Returns:
            Message ID
        """
        message = AgentMessage(
            message_type=message_type,
            source_agent=source_agent,
            target_agents=[],  # Empty = broadcast
            content=content,
            metadata=metadata or {}
        )
        return self.publish(message)
    
    def send_alert(
        self,
        content: str,
        source_agent: str,
        severity: str = "info",
        target_agents: Optional[List[str]] = None
    ) -> str:
        """
        Send an alert message.
        
        Args:
            content: Alert content
            source_agent: Agent sending the alert
            severity: Alert severity (info, warning, critical)
            target_agents: Optional specific targets
            
        Returns:
            Message ID
        """
        message = AgentMessage(
            message_type=MessageType.ALERT,
            source_agent=source_agent,
            target_agents=target_agents or [],
            content=content,
            metadata={"severity": severity}
        )
        return self.publish(message)
    
    def get_history(
        self,
        agent_name: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 10
    ) -> List[AgentMessage]:
        """
        Get message history with optional filters.
        
        Args:
            agent_name: Filter by source agent
            message_type: Filter by message type
            limit: Maximum messages to return
            
        Returns:
            List of matching messages
        """
        messages = self._history.copy()
        
        if agent_name:
            messages = [m for m in messages if m.source_agent == agent_name]
        
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        return messages[-limit:]
    
    def get_pending_count(self, agent_name: str) -> int:
        """Get count of pending messages for an agent."""
        return len(self._pending.get(agent_name, []))
