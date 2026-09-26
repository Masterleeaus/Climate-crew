"""Oracle planner that generates perfect plans."""
from typing import List, Dict, Any


class OraclePlanner:
    """Oracle planner that generates perfect plans based on ground truth."""
    
    def plan(
        self,
        query: str,
        expected_topics: List[str],
        ground_truth_answer: str
    ) -> List[Dict[str, Any]]:
        """
        Generate perfect plan based on ground truth.
        
        Args:
            query: User query
            expected_topics: Expected topics to cover
            ground_truth_answer: Ground truth answer
            
        Returns:
            List of plan items, each with:
                - topic: str
                - description: str
                - initial_search_queries: List[str]
        """
        plan = []
        
        # Create one plan item per expected topic
        for topic in expected_topics:
            plan.append({
                "topic": topic,
                "description": f"Research {topic} as it relates to: {query}",
                "initial_search_queries": [f"{query} {topic}", topic],
                "priority": 1.0,
                "oracle": True
            })
        
        # If no topics, create a single plan item from query
        if not plan:
            plan.append({
                "topic": query,
                "description": f"Research: {query}",
                "initial_search_queries": [query],
                "priority": 1.0,
                "oracle": True
            })
        
        return plan
