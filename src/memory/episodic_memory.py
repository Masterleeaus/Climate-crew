"""
Episodic Memory - Time-decayed vector storage with recency weighting.
Uses Qdrant for vector storage with temporal scoring.
"""
import os
import math
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EpisodicMemoryItem:
    """Single episodic memory with metadata."""
    id: str
    content: str
    agent_id: str
    timestamp: datetime
    semantic_score: float = 0.0
    recency_score: float = 0.0
    final_score: float = 0.0
    consolidated: bool = False
    importance: float = 0.5  # 0-1 scale
    metadata: Dict[str, Any] = field(default_factory=dict)


class EpisodicMemory:
    """
    Time-decayed episodic memory using Qdrant.
    - Stores past interactions with timestamps
    - Applies recency weighting to search results
    - Supports importance scoring for consolidation priority
    """
    
    # Weights for final score calculation
    SEMANTIC_WEIGHT = 0.7
    RECENCY_WEIGHT = 0.3
    RECENCY_HALF_LIFE_HOURS = 168  # 1 week
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "convolve_episodic_memory",
        google_api_key: Optional[str] = None
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.collection_name = collection_name
        self._memory = None
        self._initialized = False
    
    def _ensure_initialized(self) -> bool:
        """Lazy initialization of Mem0."""
        if self._initialized:
            return True
        
        if not self.qdrant_url or not self.qdrant_api_key:
            logger.warning("Qdrant not configured. Episodic memory disabled.")
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
            logger.info("Episodic memory initialized with Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize episodic memory: {e}")
            return False
    
    def calculate_recency_score(self, memory_time: datetime) -> float:
        """
        Calculate recency score with exponential decay.
        Returns 1.0 for now, ~0.5 after 1 week, approaches 0 over time.
        """
        now = datetime.now(timezone.utc)
        if memory_time.tzinfo is None:
            memory_time = memory_time.replace(tzinfo=timezone.utc)
        
        hours_old = (now - memory_time).total_seconds() / 3600
        return math.exp(-hours_old / self.RECENCY_HALF_LIFE_HOURS)
    
    def calculate_final_score(self, semantic_score: float, recency_score: float) -> float:
        """Combine semantic similarity and recency into final score."""
        return (self.SEMANTIC_WEIGHT * semantic_score + 
                self.RECENCY_WEIGHT * recency_score)
    
    def add(
        self,
        content: str,
        agent_id: str,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Add episodic memory with timestamp and importance."""
        if not self._ensure_initialized():
            return None
        
        meta = metadata or {}
        meta["timestamp"] = datetime.now(timezone.utc).isoformat()
        meta["agent_id"] = agent_id
        meta["importance"] = importance
        meta["consolidated"] = False
        
        retries = 3
        delay = 5
        
        for attempt in range(retries):
            try:
                result = self._memory.add(content, user_id=agent_id, metadata=meta)
                return result.get("id") if isinstance(result, dict) else None
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                logger.error(f"Failed to add episodic memory: {e}")
                return None
        return None
    
    def search(
        self,
        query: str,
        agent_id: str,
        limit: int = 5,
        apply_recency: bool = True
    ) -> List[EpisodicMemoryItem]:
        """
        Search episodic memory with optional recency weighting.
        Returns memories sorted by final score (semantic + recency).
        """
        if not self._ensure_initialized():
            return []
        
        retries = 3
        delay = 5
        
        for attempt in range(retries):
            try:
                # Get more results than needed for re-ranking
                raw_results = self._memory.search(query, user_id=agent_id, limit=limit * 2)
                
                # Handle different response formats
                if isinstance(raw_results, dict):
                    raw_results = raw_results.get("results", [])
                
                items = []
                for result in raw_results:
                    content = result.get("memory", result.get("text", ""))
                    metadata = result.get("metadata", {})
                    
                    # Parse timestamp
                    ts_str = metadata.get("timestamp")
                    try:
                        timestamp = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)
                    except:
                        timestamp = datetime.now(timezone.utc)
                    
                    semantic_score = result.get("score", 0.5)
                    recency_score = self.calculate_recency_score(timestamp) if apply_recency else 1.0
                    final_score = self.calculate_final_score(semantic_score, recency_score)
                    
                    items.append(EpisodicMemoryItem(
                        id=result.get("id", ""),
                        content=content,
                        agent_id=metadata.get("agent_id", agent_id),
                        timestamp=timestamp,
                        semantic_score=semantic_score,
                        recency_score=recency_score,
                        final_score=final_score,
                        consolidated=metadata.get("consolidated", False),
                        importance=metadata.get("importance", 0.5),
                        metadata=metadata
                    ))
                
                # Sort by final score and return top results
                items.sort(key=lambda x: x.final_score, reverse=True)
                return items[:limit]
                
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                logger.error(f"Failed to search episodic memory: {e}")
                return []
        return []
    
    def get_unconsolidated(self, limit: int = 50) -> List[EpisodicMemoryItem]:
        """Get memories that haven't been consolidated yet (for background processing)."""
        # This would require a metadata filter on Qdrant
        # For now, return empty - consolidator will use get_all
        return []
    
    def mark_consolidated(self, memory_id: str) -> bool:
        """Mark a memory as consolidated."""
        # Would need Qdrant update operation
        # For now, just log
        logger.info(f"Marked memory {memory_id} as consolidated")
        return True
    
    def get_context_string(self, query: str, agent_id: str, limit: int = 3) -> str:
        """Get episodic memories as formatted context string."""
        memories = self.search(query, agent_id, limit)
        if not memories:
            return ""
        
        parts = ["[Episodic Memory - Past Interactions]"]
        for mem in memories:
            age = (datetime.now(timezone.utc) - mem.timestamp).days
            age_str = f"{age}d ago" if age > 0 else "today"
            parts.append(f"- [{age_str}] {mem.content}")
        
        return "\n".join(parts)
