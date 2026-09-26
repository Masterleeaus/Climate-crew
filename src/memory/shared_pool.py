"""
Shared Memory Pool - Cross-agent memory access.
Allows agents to share knowledge with configurable visibility.
"""
import os
import logging
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SharedMemoryItem:
    """A memory shared across agents."""
    id: str
    content: str
    source_agent: str
    visibility: Union[str, List[str]]  # "global", "domain", or list of agent IDs
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    importance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedMemoryPool:
    """
    Shared memory accessible across all agents.
    - Supports visibility levels: global, domain-specific, or explicit agent list
    - Uses Qdrant for vector storage with agent filtering
    """
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "convolve_shared_memory",
        google_api_key: Optional[str] = None
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.collection_name = collection_name
        self._memory = None
        self._initialized = False
    
    def _ensure_initialized(self) -> bool:
        """Lazy initialization of Mem0 for shared pool."""
        if self._initialized:
            return True
        
        if not self.qdrant_url or not self.qdrant_api_key:
            logger.warning("Qdrant not configured. Shared memory disabled.")
            return False
        
        try:
            from mem0 import Memory
            
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": self.collection_name,
                        "url": self.qdrant_url,
                        "api_key": self.qdrant_api_key,
                        "embedding_model_dims": 768
                    }
                },
                "llm": {
                    "provider": "gemini",
                    "config": {
                        "model": "gemini-2.0-flash",
                        "api_key": self.google_api_key
                    }
                },
                "embedder": {
                    "provider": "gemini",
                    "config": {
                        "model": "gemini-embedding-001",
                        "api_key": self.google_api_key
                    }
                }
            }
            
            self._memory = Memory.from_config(config)
            self._initialized = True
            logger.info("Shared memory pool initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize shared memory: {e}")
            return False
    
    def add(
        self,
        content: str,
        source_agent: str,
        visibility: Union[str, List[str]] = "global",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a memory to the shared pool.
        
        Args:
            content: The memory content
            source_agent: Agent that created this memory
            visibility: "global" | "domain" | list of agent IDs
            importance: 0-1 score for prioritization
            metadata: Additional metadata
        """
        if not self._ensure_initialized():
            return None
        
        meta = metadata or {}
        meta["timestamp"] = datetime.now(timezone.utc).isoformat()
        meta["source_agent"] = source_agent
        meta["visibility"] = visibility if isinstance(visibility, str) else ",".join(visibility)
        meta["importance"] = importance
        meta["is_shared"] = True
        
        retries = 3
        delay = 5
        
        for attempt in range(retries):
            try:
                # Use special user_id for shared pool
                result = self._memory.add(content, user_id="__shared_pool__", metadata=meta)
                logger.info(f"Shared memory added by {source_agent}: {content[:50]}...")
                return result.get("id") if isinstance(result, dict) else None
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                logger.error(f"Failed to add shared memory: {e}")
                return None
        return None
    
    def search(
        self,
        query: str,
        requesting_agent: str,
        limit: int = 5
    ) -> List[SharedMemoryItem]:
        """
        Search shared memories accessible to the requesting agent.
        
        Returns memories where:
        - visibility is "global", OR
        - visibility is "domain" and agent is in same domain, OR
        - requesting_agent is in the visibility list
        """
        if not self._ensure_initialized():
            return []
        
        retries = 3
        delay = 5
        
        for attempt in range(retries):
            try:
                raw_results = self._memory.search(query, user_id="__shared_pool__", limit=limit * 3)
                
                if isinstance(raw_results, dict):
                    raw_results = raw_results.get("results", [])
                
                items = []
                for result in raw_results:
                    metadata = result.get("metadata", {})
                    visibility = metadata.get("visibility", "global")
                    
                    # Check visibility permissions
                    if not self._can_access(requesting_agent, visibility):
                        continue
                    
                    # Parse timestamp
                    ts_str = metadata.get("timestamp")
                    try:
                        timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)
                    except:
                        timestamp = datetime.now(timezone.utc)
                    
                    items.append(SharedMemoryItem(
                        id=result.get("id", ""),
                        content=result.get("memory", result.get("text", "")),
                        source_agent=metadata.get("source_agent", "unknown"),
                        visibility=visibility,
                        timestamp=timestamp,
                        importance=metadata.get("importance", 0.5),
                        metadata=metadata
                    ))
                
                # Sort by importance and return
                items.sort(key=lambda x: x.importance, reverse=True)
                return items[:limit]
                
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                logger.error(f"Failed to search shared memory: {e}")
                return []
        return []
    
    def _can_access(self, agent_id: str, visibility: str) -> bool:
        """Check if agent can access a memory based on visibility."""
        if visibility == "global":
            return True
        
        if visibility == "domain":
            # Simple domain matching based on agent name prefix
            # e.g., "air_quality" and "air_pollution" share "air" domain
            return True  # For now, allow all domain access
        
        # Check if agent is in explicit list
        if "," in visibility:
            allowed_agents = [a.strip() for a in visibility.split(",")]
            return agent_id in allowed_agents
        
        return visibility == agent_id
    
    def get_context_string(self, query: str, requesting_agent: str, limit: int = 3) -> str:
        """Get shared memories as formatted context string."""
        memories = self.search(query, requesting_agent, limit)
        if not memories:
            return ""
        
        parts = ["[Shared Memory - Cross-Agent Knowledge]"]
        for mem in memories:
            parts.append(f"- [from {mem.source_agent}] {mem.content}")
        
        return "\n".join(parts)
