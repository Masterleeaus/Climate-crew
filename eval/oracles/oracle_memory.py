"""Oracle memory that returns perfect memory context."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..types import MemoryOperation


class OracleMemory:
    """Oracle memory that returns perfect memory context."""
    
    def __init__(self, ground_truth_memories: Dict[str, Any]):
        """
        Initialize oracle memory.
        
        Args:
            ground_truth_memories: Dict mapping keys to memory values
        """
        self.ground_truth_memories = ground_truth_memories
    
    def retrieve(
        self,
        query: str,
        expected_topics: List[str]
    ) -> List[MemoryOperation]:
        """
        Retrieve perfect memories based on ground truth.
        
        Args:
            query: Current query
            expected_topics: Expected topics
            
        Returns:
            List of MemoryOperation for retrieved memories
        """
        operations = []
        
        # Return memories that match expected topics
        for key, value in self.ground_truth_memories.items():
            value_str = str(value).lower()
            # Check if memory is relevant to query or topics
            query_lower = query.lower()
            topics_lower = " ".join(expected_topics).lower()
            
            if query_lower in value_str or any(topic.lower() in value_str for topic in expected_topics):
                operations.append(MemoryOperation(
                    operation_type="retrieve",
                    key=key,
                    value=value,
                    timestamp=datetime.now(),
                    metadata={"oracle": True}
                ))
        
        return operations
    
    def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryOperation:
        """
        Store memory (oracle always succeeds).
        
        Args:
            key: Memory key
            value: Memory value
            metadata: Optional metadata
            
        Returns:
            MemoryOperation for stored memory
        """
        return MemoryOperation(
            operation_type="store",
            key=key,
            value=value,
            timestamp=datetime.now(),
            metadata={"oracle": True, **(metadata or {})}
        )
