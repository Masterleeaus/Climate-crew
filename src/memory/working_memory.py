"""
Working Memory - Session-level buffer for immediate context.
Stores active conversation context and tool results for the current session.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkingMemoryItem:
    """Single item in working memory."""
    content: str
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    item_type: str = "context"  # "context", "tool_result", "user_query"
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkingMemory:
    """
    Session-level memory buffer.
    - Cleared when session ends
    - Fast in-memory access
    - Limited capacity (FIFO eviction)
    """
    
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self._buffer: List[WorkingMemoryItem] = []
        self._session_id: Optional[str] = None
    
    def start_session(self, session_id: str):
        """Start a new session, clearing old buffer."""
        self._session_id = session_id
        self._buffer.clear()
        logger.info(f"Working memory session started: {session_id}")
    
    def add(
        self, 
        content: str, 
        agent_id: str, 
        item_type: str = "context",
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkingMemoryItem:
        """Add item to working memory buffer."""
        item = WorkingMemoryItem(
            content=content,
            agent_id=agent_id,
            item_type=item_type,
            metadata=metadata or {}
        )
        
        self._buffer.append(item)
        
        # FIFO eviction if over capacity
        if len(self._buffer) > self.max_items:
            evicted = self._buffer.pop(0)
            logger.debug(f"Evicted oldest working memory item: {evicted.content[:50]}...")
        
        return item
    
    def get_recent(self, limit: int = 10, agent_id: Optional[str] = None) -> List[WorkingMemoryItem]:
        """Get most recent items, optionally filtered by agent."""
        items = self._buffer
        if agent_id:
            items = [item for item in items if item.agent_id == agent_id]
        return items[-limit:]
    
    def get_context_string(self, limit: int = 5, agent_id: Optional[str] = None) -> str:
        """Get recent items as formatted context string."""
        items = self.get_recent(limit, agent_id)
        if not items:
            return ""
        
        parts = ["[Working Memory - Current Session]"]
        for item in items:
            prefix = f"[{item.item_type.upper()}]" if item.item_type != "context" else "-"
            parts.append(f"{prefix} {item.content}")
        
        return "\n".join(parts)
    
    def search(self, query: str, limit: int = 5) -> List[WorkingMemoryItem]:
        """Simple keyword search in working memory (no embeddings needed)."""
        query_lower = query.lower()
        matches = []
        
        for item in reversed(self._buffer):  # Most recent first
            if query_lower in item.content.lower():
                matches.append(item)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def clear(self):
        """Clear all working memory."""
        self._buffer.clear()
        logger.info("Working memory cleared")
    
    def __len__(self) -> int:
        return len(self._buffer)
