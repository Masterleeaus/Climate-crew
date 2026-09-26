"""
Meta-Learning System - Learns from past routing decisions to improve agent selection.
Provides intelligent suggestions based on query similarity and historical performance.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import dataclass

from ..memory.performance_store import PerformanceStore, RoutingRecord, AgentStats

logger = logging.getLogger(__name__)


@dataclass
class RoutingSuggestion:
    """A suggestion from the meta-learner for which agent to use."""
    agent_name: str
    confidence: float  # 0-1
    reasoning: str
    similar_queries: List[str]  # Past queries that informed this decision
    historical_quality: float  # Average quality for this agent on similar queries


class MetaLearner:
    """
    Meta-learning system that improves routing decisions over time.
    
    Learning mechanism:
    1. Records every routing decision with its outcome (quality score)
    2. When a new query arrives, finds similar past queries
    3. Suggests agents based on weighted historical performance
    4. Continuously updates agent performance profiles
    """
    
    def __init__(
        self,
        performance_store: Optional[PerformanceStore] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        similarity_threshold: float = 0.6,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize the meta-learner.
        
        Args:
            performance_store: Existing store or creates new one
            similarity_threshold: Minimum similarity for considering past queries
            confidence_threshold: Minimum confidence to make a strong suggestion
        """
        self.store = performance_store or PerformanceStore(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            google_api_key=google_api_key
        )
        
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold
        
        # Cache for agent capabilities (loaded from registry)
        self._agent_capabilities: Dict[str, Dict] = {}
        
        logger.info("MetaLearner initialized")
    
    def suggest_agent(
        self,
        query: str,
        available_agents: Optional[List[str]] = None
    ) -> RoutingSuggestion:
        """
        Suggest the best agent for a query based on historical performance.
        
        Args:
            query: The user query to route
            available_agents: Optional filter for which agents to consider
            
        Returns:
            RoutingSuggestion with agent recommendation and confidence
        """
        # Search for similar past queries
        similar_records = self.store.search_similar(
            query,
            limit=10,
            min_score=self.similarity_threshold
        )
        
        if not similar_records:
            # No historical data - return low-confidence suggestion
            return RoutingSuggestion(
                agent_name="",
                confidence=0.0,
                reasoning="No similar past queries found. Recommending LLM-based routing.",
                similar_queries=[],
                historical_quality=0.0
            )
        
        # Aggregate scores by agent
        agent_scores: Dict[str, Dict] = {}
        
        for record, similarity in similar_records:
            agent = record.selected_agent
            
            # Filter agents if specified
            if available_agents and agent not in available_agents:
                continue
            
            if agent not in agent_scores:
                agent_scores[agent] = {
                    "weighted_quality_sum": 0.0,
                    "similarity_sum": 0.0,
                    "count": 0,
                    "queries": []
                }
            
            # Weight quality by similarity (more similar = more weight)
            agent_scores[agent]["weighted_quality_sum"] += similarity * record.response_quality
            agent_scores[agent]["similarity_sum"] += similarity
            agent_scores[agent]["count"] += 1
            agent_scores[agent]["queries"].append(record.query[:50])
        
        if not agent_scores:
            return RoutingSuggestion(
                agent_name="",
                confidence=0.0,
                reasoning="No matching agents found in history.",
                similar_queries=[],
                historical_quality=0.0
            )
        
        # Calculate weighted average quality for each agent
        agent_rankings: List[Tuple[str, float, Dict]] = []
        
        for agent, scores in agent_scores.items():
            weighted_avg = scores["weighted_quality_sum"] / scores["similarity_sum"]
            
            # Boost confidence with more data points
            data_confidence = min(1.0, scores["count"] / 5)  # Max confidence at 5+ examples
            
            final_confidence = weighted_avg * data_confidence
            agent_rankings.append((agent, final_confidence, scores))
        
        # Sort by confidence
        agent_rankings.sort(key=lambda x: x[1], reverse=True)
        
        best_agent, best_confidence, best_scores = agent_rankings[0]
        
        return RoutingSuggestion(
            agent_name=best_agent,
            confidence=best_confidence,
            reasoning=f"Based on {best_scores['count']} similar past queries with avg quality {best_scores['weighted_quality_sum']/best_scores['similarity_sum']:.2f}",
            similar_queries=best_scores["queries"][:3],
            historical_quality=best_scores["weighted_quality_sum"] / best_scores["similarity_sum"]
        )
    
    def record_outcome(
        self,
        query: str,
        selected_agent: str,
        response_quality: float,
        latency_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Record a routing outcome for future learning.
        
        Args:
            query: The original query
            selected_agent: Which agent handled it
            response_quality: Quality score (0-1) from reflexion
            latency_ms: Response latency
            success: Whether the response was successful
            metadata: Additional context
            
        Returns:
            Record ID if stored successfully
        """
        try:
            # Generate embedding for query
            query_embedding = self.store.get_embedding(query)
            
            if not query_embedding:
                logger.warning("Failed to generate embedding for query")
                return None
            
            record = RoutingRecord(
                id="",  # Will be generated
                query=query,
                query_embedding=query_embedding,
                selected_agent=selected_agent,
                response_quality=response_quality,
                latency_ms=latency_ms,
                success=success,
                metadata=metadata or {}
            )
            
            return self.store.add(record)
            
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
            return None
    
    def get_agent_performance(self, agent_name: str) -> Optional[AgentStats]:
        """Get aggregate performance metrics for an agent."""
        return self.store.get_agent_stats(agent_name)
    
    def get_all_agent_performance(self) -> Dict[str, AgentStats]:
        """Get performance metrics for all agents."""
        return self.store.get_all_agent_stats()
    
    def should_use_suggestion(self, suggestion: RoutingSuggestion) -> bool:
        """Determine if the suggestion confidence is high enough to use directly."""
        return suggestion.confidence >= self.confidence_threshold
    
    def get_routing_insights(self, query: str) -> Dict[str, Any]:
        """
        Get detailed insights about routing for a query.
        Useful for debugging and understanding decisions.
        """
        suggestion = self.suggest_agent(query)
        all_stats = self.get_all_agent_performance()
        
        return {
            "suggested_agent": suggestion.agent_name,
            "confidence": suggestion.confidence,
            "reasoning": suggestion.reasoning,
            "similar_past_queries": suggestion.similar_queries,
            "all_agent_stats": {
                name: {
                    "total_queries": stats.total_queries,
                    "avg_quality": round(stats.avg_quality, 3),
                    "avg_latency_ms": round(stats.avg_latency_ms, 1),
                    "success_rate": round(stats.success_rate, 3)
                }
                for name, stats in all_stats.items()
            }
        }
