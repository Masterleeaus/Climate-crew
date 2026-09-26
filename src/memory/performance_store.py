"""
Performance Store - Persistent storage for agent routing metrics.
Uses Qdrant for embedding-based similarity search on past queries.
"""
import os
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class RoutingRecord:
    """Record of a single routing decision and its outcome."""
    id: str
    query: str
    query_embedding: List[float]
    selected_agent: str
    response_quality: float  # 0-1 from reflexion score
    latency_ms: float
    success: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStats:
    """Aggregate performance statistics for an agent."""
    agent_name: str
    total_queries: int = 0
    avg_quality: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    quality_sum: float = 0.0
    latency_sum: float = 0.0
    success_count: int = 0
    
    def update(self, quality: float, latency_ms: float, success: bool):
        """Update running statistics with new observation."""
        self.total_queries += 1
        self.quality_sum += quality
        self.latency_sum += latency_ms
        if success:
            self.success_count += 1
        
        # Recalculate averages
        self.avg_quality = self.quality_sum / self.total_queries
        self.avg_latency_ms = self.latency_sum / self.total_queries
        self.success_rate = self.success_count / self.total_queries


class PerformanceStore:
    """
    Persistent storage for routing history using Qdrant vector search.
    Enables similarity-based retrieval of past routing decisions.
    """
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "convolve_routing_history",
        google_api_key: Optional[str] = None
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.collection_name = collection_name
        
        self._client = None
        self._embedder = None
        self._initialized = False
        
        # In-memory agent statistics (also persists key metrics to Qdrant metadata)
        self._agent_stats: Dict[str, AgentStats] = {}
    
    def _ensure_initialized(self) -> bool:
        """Lazy initialization of Qdrant client and embedder."""
        if self._initialized:
            return True
        
        if not self.qdrant_url or not self.qdrant_api_key:
            logger.warning("Qdrant not configured. Performance store disabled.")
            return False
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            import google.generativeai as genai
            
            # Initialize Qdrant client
            self._client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key
            )
            
            # Initialize Gemini embedder
            genai.configure(api_key=self.google_api_key)
            
            # Ensure collection exists
            collections = [c.name for c in self._client.get_collections().collections]
            if self.collection_name not in collections:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.collection_name}")
            
            self._initialized = True
            logger.info("Performance store initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize performance store: {e}")
            return False
    
    def _embed(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini."""
        import google.generativeai as genai
        
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text
        )
        return result['embedding']
    
    def add(self, record: RoutingRecord) -> Optional[str]:
        """
        Add a routing record to the store.
        
        Args:
            record: The routing record to store
            
        Returns:
            Record ID if successful, None otherwise
        """
        if not self._ensure_initialized():
            return None
        
        try:
            from qdrant_client.models import PointStruct
            
            # Generate ID if not provided
            if not record.id:
                record.id = str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                "query": record.query,
                "selected_agent": record.selected_agent,
                "response_quality": record.response_quality,
                "latency_ms": record.latency_ms,
                "success": record.success,
                "timestamp": record.timestamp.isoformat(),
                **record.metadata
            }
            
            # Upsert to Qdrant
            self._client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=record.id,
                        vector=record.query_embedding,
                        payload=payload
                    )
                ]
            )
            
            # Update agent stats
            self._update_agent_stats(
                record.selected_agent,
                record.response_quality,
                record.latency_ms,
                record.success
            )
            
            logger.info(f"Stored routing record: {record.id} -> {record.selected_agent}")
            return record.id
            
        except Exception as e:
            logger.error(f"Failed to add routing record: {e}")
            return None
    
    def search_similar(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.5
    ) -> List[Tuple[RoutingRecord, float]]:
        """
        Search for similar past queries.
        
        Args:
            query: The query to search for
            limit: Maximum number of results
            min_score: Minimum similarity score threshold
            
        Returns:
            List of (RoutingRecord, similarity_score) tuples
        """
        if not self._ensure_initialized():
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self._embed(query)
            
            # Search Qdrant (use query_points for newer qdrant-client versions)
            from qdrant_client.models import Filter
            
            results = self._client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                score_threshold=min_score
            ).points
            
            records = []
            for result in results:
                payload = result.payload
                record = RoutingRecord(
                    id=str(result.id),
                    query=payload.get("query", ""),
                    query_embedding=query_embedding,  # Not stored in payload
                    selected_agent=payload.get("selected_agent", ""),
                    response_quality=payload.get("response_quality", 0.0),
                    latency_ms=payload.get("latency_ms", 0.0),
                    success=payload.get("success", True),
                    timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.now(timezone.utc).isoformat())),
                    metadata={k: v for k, v in payload.items() if k not in 
                             ["query", "selected_agent", "response_quality", "latency_ms", "success", "timestamp"]}
                )
                records.append((record, result.score))
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to search similar queries: {e}")
            return []
    
    def _update_agent_stats(
        self,
        agent_name: str,
        quality: float,
        latency_ms: float,
        success: bool
    ):
        """Update in-memory agent statistics."""
        if agent_name not in self._agent_stats:
            self._agent_stats[agent_name] = AgentStats(agent_name=agent_name)
        
        self._agent_stats[agent_name].update(quality, latency_ms, success)
    
    def get_agent_stats(self, agent_name: str) -> Optional[AgentStats]:
        """Get aggregate statistics for an agent."""
        return self._agent_stats.get(agent_name)
    
    def get_all_agent_stats(self) -> Dict[str, AgentStats]:
        """Get statistics for all agents."""
        return self._agent_stats.copy()
    
    def get_embedding(self, text: str) -> List[float]:
        """Public method to generate embeddings."""
        if not self._ensure_initialized():
            return []
        return self._embed(text)
