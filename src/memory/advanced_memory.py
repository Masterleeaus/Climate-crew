"""
Advanced Memory Manager - Unified interface for hierarchical + shared memory.
Integrates working, episodic, semantic, and shared memory tiers.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .working_memory import WorkingMemory, WorkingMemoryItem
from .episodic_memory import EpisodicMemory, EpisodicMemoryItem
from .semantic_memory import SemanticMemory, Entity, Relationship, Fact
from .shared_pool import SharedMemoryPool, SharedMemoryItem

logger = logging.getLogger(__name__)


@dataclass
class MemorySearchResult:
    """Unified search result from any memory tier."""
    content: str
    source_tier: str  # "working", "episodic", "semantic", "shared"
    score: float
    agent_id: str
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedMemoryManager:
    """
    Unified interface for hierarchical memory system.
    
    Memory Tiers:
    - Working: Session buffer (in-memory, fast, temporary)
    - Episodic: Past interactions with recency decay (Qdrant)
    - Semantic: Permanent facts and relationships (Neo4j)
    - Shared: Cross-agent knowledge pool (Qdrant)
    """
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        neo4j_url: Optional[str] = None,
        neo4j_username: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        google_api_key: Optional[str] = None,
        enable_working: bool = True,
        enable_episodic: bool = True,
        enable_semantic: bool = True,
        enable_shared: bool = True
    ):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize memory tiers based on flags
        self.working = WorkingMemory() if enable_working else None
        
        self.episodic = EpisodicMemory(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            google_api_key=self.google_api_key
        ) if enable_episodic else None
        
        self.semantic = SemanticMemory(
            neo4j_url=neo4j_url,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password
        ) if enable_semantic else None
        
        self.shared = SharedMemoryPool(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            google_api_key=self.google_api_key
        ) if enable_shared else None
        
        logger.info(f"Advanced memory initialized: working={enable_working}, "
                   f"episodic={enable_episodic}, semantic={enable_semantic}, shared={enable_shared}")
    
    # ========== WORKING MEMORY ==========
    
    def add_to_working(
        self,
        content: str,
        agent_id: str,
        item_type: str = "context"
    ) -> Optional[WorkingMemoryItem]:
        """Add to session buffer."""
        if self.working is None:
            return None
        return self.working.add(content, agent_id, item_type)
    
    def get_working_context(self, limit: int = 5, agent_id: Optional[str] = None) -> str:
        """Get working memory as context string."""
        if self.working is None:
            return ""
        return self.working.get_context_string(limit, agent_id)
    
    # ========== EPISODIC MEMORY ==========
    
    def add_to_episodic(
        self,
        content: str,
        agent_id: str,
        importance: float = 0.5,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Add to time-decayed episodic memory."""
        if self.episodic is None:
            return None
        return self.episodic.add(content, agent_id, importance, metadata)
    
    def search_episodic(
        self,
        query: str,
        agent_id: str,
        limit: int = 5
    ) -> List[EpisodicMemoryItem]:
        """Search episodic memory with recency weighting."""
        if self.episodic is None:
            return []
        return self.episodic.search(query, agent_id, limit)
    
    # ========== SEMANTIC MEMORY ==========
    
    def add_entity(self, entity: Entity) -> bool:
        """Add permanent entity to semantic memory."""
        if not self.semantic:
            return False
        return self.semantic.add_entity(entity)
    
    def add_relationship(self, relationship: Relationship) -> bool:
        """Add relationship between entities."""
        if not self.semantic:
            return False
        return self.semantic.add_relationship(relationship)
    
    def add_fact(self, fact: Fact) -> bool:
        """Add permanent fact to semantic memory."""
        if not self.semantic:
            return False
        return self.semantic.add_fact(fact)
    
    def search_entity(self, name: str) -> Optional[Dict]:
        """Search for an entity and its knowledge."""
        if not self.semantic:
            return None
        return self.semantic.search_entity(name)
    
    # ========== SHARED MEMORY ==========
    
    def share(
        self,
        content: str,
        source_agent: str,
        visibility: Union[str, List[str]] = "global",
        importance: float = 0.5
    ) -> Optional[str]:
        """Share memory to cross-agent pool."""
        if self.shared is None:
            return None
        return self.shared.add(content, source_agent, visibility, importance)
    
    def search_shared(
        self,
        query: str,
        requesting_agent: str,
        limit: int = 5
    ) -> List[SharedMemoryItem]:
        """Search shared memory pool."""
        if self.shared is None:
            return []
        return self.shared.search(query, requesting_agent, limit)
    
    # ========== UNIFIED SEARCH ==========
    
    def search(
        self,
        query: str,
        agent_id: str,
        limit: int = 5,
        include_working: bool = True,
        include_episodic: bool = True,
        include_shared: bool = True
    ) -> List[MemorySearchResult]:
        """
        Unified search across all memory tiers.
        Returns combined results sorted by score.
        """
        results = []
        
        # Search working memory
        if include_working and self.working:
            for item in self.working.search(query, limit):
                results.append(MemorySearchResult(
                    content=item.content,
                    source_tier="working",
                    score=1.0,  # Working memory is most recent
                    agent_id=item.agent_id,
                    timestamp=item.timestamp
                ))
        
        # Search episodic memory
        if include_episodic and self.episodic:
            for item in self.episodic.search(query, agent_id, limit):
                results.append(MemorySearchResult(
                    content=item.content,
                    source_tier="episodic",
                    score=item.final_score,
                    agent_id=item.agent_id,
                    timestamp=item.timestamp,
                    metadata={"recency_score": item.recency_score}
                ))
        
        # Search shared memory
        if include_shared and self.shared:
            for item in self.shared.search(query, agent_id, limit):
                results.append(MemorySearchResult(
                    content=item.content,
                    source_tier="shared",
                    score=item.importance,
                    agent_id=item.source_agent,
                    timestamp=item.timestamp
                ))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def get_context_string(
        self,
        query: str,
        agent_id: str,
        limit: int = 3
    ) -> str:
        """
        Get combined context string from all memory tiers.
        Suitable for injecting into LLM prompts.
        """
        parts = []
        
        # Working memory (most relevant for current context)
        if self.working:
            working_ctx = self.working.get_context_string(limit, agent_id)
            if working_ctx:
                parts.append(working_ctx)
        
        # Episodic memory (past interactions)
        if self.episodic:
            episodic_ctx = self.episodic.get_context_string(query, agent_id, limit)
            if episodic_ctx:
                parts.append(episodic_ctx)
        
        # Shared memory (cross-agent knowledge)
        if self.shared:
            shared_ctx = self.shared.get_context_string(query, agent_id, limit)
            if shared_ctx:
                parts.append(shared_ctx)
        
        return "\n\n".join(parts)
    
    # ========== LEGACY COMPATIBILITY ==========
    
    def add(
        self,
        content: str,
        agent_id: str,
        metadata: Optional[Dict] = None,
        tier: str = "episodic"
    ) -> Optional[str]:
        """
        Legacy add method for backward compatibility.
        Defaults to episodic tier.
        """
        if tier == "working":
            item = self.add_to_working(content, agent_id)
            return "working" if item else None
        elif tier == "episodic":
            return self.add_to_episodic(content, agent_id, 0.5, metadata)
        elif tier == "shared":
            return self.share(content, agent_id)
        return None
    
    def get_context(self, query: str, agent_id: str, limit: int = 3) -> str:
        """Legacy context method for backward compatibility."""
        return self.get_context_string(query, agent_id, limit)
    
    def clear_agent_memories(self, agent_id: str) -> bool:
        """Clear all memories for an agent."""
        if self.working:
            self.working.clear()
        # Episodic and shared would need delete methods
        return True
