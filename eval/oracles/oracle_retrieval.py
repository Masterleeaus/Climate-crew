"""Oracle retrieval that returns perfect results."""
from typing import List, Dict, Any
from ..types import RetrievalResult


class OracleRetrieval:
    """Oracle retrieval that returns perfect results based on ground truth."""
    
    def __init__(self, ground_truth_docs: Dict[str, str]):
        """
        Initialize oracle retrieval.
        
        Args:
            ground_truth_docs: Dict mapping document_id to content
        """
        self.ground_truth_docs = ground_truth_docs
    
    def retrieve(
        self,
        query: str,
        expected_topics: List[str],
        limit: int = 5
    ) -> List[RetrievalResult]:
        """
        Retrieve perfect documents based on ground truth.
        
        Args:
            query: Search query
            expected_topics: Expected topics (used to select relevant docs)
            limit: Maximum number of results
            
        Returns:
            List of RetrievalResult with perfect relevance
        """
        # Select documents that match expected topics
        relevant_docs = []
        
        for doc_id, content in self.ground_truth_docs.items():
            content_lower = content.lower()
            # Check if document contains any expected topic
            matches = sum(1 for topic in expected_topics if topic.lower() in content_lower)
            if matches > 0:
                relevant_docs.append((doc_id, content, matches))
        
        # Sort by number of topic matches (descending)
        relevant_docs.sort(key=lambda x: x[2], reverse=True)
        
        # Return top results
        results = []
        for i, (doc_id, content, score) in enumerate(relevant_docs[:limit]):
            results.append(RetrievalResult(
                document_id=doc_id,
                content=content,
                score=1.0 - (i * 0.1),  # Perfect scores, slightly decreasing
                rank=i + 1,
                metadata={"oracle": True, "topic_matches": score}
            ))
        
        return results
